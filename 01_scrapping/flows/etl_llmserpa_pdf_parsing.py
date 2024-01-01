#!/usr/bin/env python3

"""
ETL Pipeline for PDF Parsing with llmsherpa

This script defines a Prefect flow for parsing PDF documents using llmsherpa.
The flow includes a task for parsing PDF and saving the extracted information to a CSV file.

Tasks:
- Parse PDF: Utilizes llmsherpa API to parse PDF documents and extracts chunks and sections.
  The extracted information is saved to a CSV file.

Prefect Flow:
- omdena_ungdc_etl_pdf_parsing_parent: Orchestrates the PDF parsing process for multiple files.
  - Reads file information from an AWS S3 bucket.
  - Parses each PDF using llmsherpa and extracts chunks and sections.
  - Saves the extracted information to a CSV file.

Note: Ensure that the 'llmsherpa', 'prefect', and 'prefect_aws' packages are installed for proper execution.
"""

import os
from pathlib import Path

import pandas as pd
from llmsherpa.readers import LayoutPDFReader

from prefect import flow, task
from prefect_aws import S3Bucket

from etl_common import read_AWS, write_AWS, get_arguments
# from llama_index import VectorStoreIndex


@task(name="LLMsherpa Parse PDF", log_prints=True)
def parse_PDF(pdf_reader:LayoutPDFReader, file_path: Path, pd_chunks: pd.DataFrame, file_infos:pd.DataFrame):
    """
    Task to parse PDF documents using llmsherpa API.

    Parameters:
    - pdf_reader (LayoutPDFReader): The LLMsherpa reader instance
    - file_path (str): Path to the PDF file to be parsed.
    - pd_chunks (pd.DataFrame): The pandas dataframe to store the extracted infos.
    - file_infos (pd.DataFrame): Information about the file being processed.

    Returns:
    pd.DataFrame: The modified pandas dataframe.
    """

    doc = pdf_reader.read_pdf(str(file_path))

    old_header = None
    bloc_text = ""
    bloc_indexes = []
    index = pd_chunks.shape[0]

    for j, chunk in enumerate(doc.chunks()):

        # header = chunk.parent.to_text()
        header = chunk.to_context_text().split('\n')[0]
        page = chunk.page_idx
        level = chunk.level
        text = chunk.to_text()
        text_w_context = chunk.to_context_text()
        text_w_context_clean = text_w_context.replace(header or "", '')

        if header is None:
            text = text_w_context_clean

        new_line = {
            "file_hash": file_infos.file_hash,
            'file_name':os.path.split(file_path)[-1],
            "page": page,
            "level": level,
            "type": None,
            "header": header,
            "chunk": chunk.to_text(),
            "bloc": "X"
            # "header_chunk": chunk.to_context_text(),
        }
        pd_chunks = pd.concat([pd_chunks, pd.DataFrame([new_line])], axis='index', ignore_index=True)

        if old_header != header:
            pd_chunks.loc[bloc_indexes, 'bloc'] = bloc_text
            old_header = header
            bloc_text = text_w_context_clean
            bloc_indexes = []
        else:
            bloc_text += text_w_context_clean

        bloc_indexes.append(index)
        index += 1

        if j == len(doc.chunks())-1:
            pd_chunks.loc[bloc_indexes, 'bloc'] = bloc_text

    return pd_chunks


@flow(log_prints=True)
def omdena_ungdc_etl_llmsherpa_pdf_parsing_parent(max_doc:int = None) -> None:
    """
    Prefect flow for orchestrating PDF parsing using llmsherpa.

    Parameters:
    - max_doc (int): The maximum number of documents to process

    Returns:
    None
    """
    print("ETL | PDF parsing")

    # Get the list of files to ingest
    bucket_block = S3Bucket.load("omdena-un-gdc-bucket")

    local_dir = "data"
    if not os.path.exists(local_dir):
        raise Exception("The source folder doesn't exist")

    files_tracker_path = Path(local_dir, "files_tracker.csv")
    if not os.path.exists(files_tracker_path):
        read_AWS(files_tracker_path, files_tracker_path, bucket_block)
    files_tracker = pd.read_csv(files_tracker_path)

    # Define the file to save the chunks
    pd_chunk_path = Path(local_dir, "extracted_chunks.csv")
    if not os.path.exists(pd_chunk_path):
        read_AWS(pd_chunk_path, pd_chunk_path, bucket_block)

    if os.path.exists(pd_chunk_path):
        pd_chunks = pd.read_csv(pd_chunk_path)
    else:
        columns = ['file_hash','file_name','page','level','type','header','chunk','bloc']
        pd_chunks = pd.DataFrame(columns=columns)

    # Define LLMsherpa parser
    llmsherpa_api = "https://readers.llmsherpa.com/api/document/developer/parseDocument?renderFormat=all"
    pdf_reader = LayoutPDFReader(llmsherpa_api)

    # Iterate through files and parse PDF
    i = 0
    for file in files_tracker.itertuples():
        if file.present_in_last_update is True and file.parsed is False: # ⚠️ 

            # Parse PDF using LLMsherpa
            file_path = Path("data", file.file_name)
            pd_chunks = parse_PDF(pdf_reader, file_path, pd_chunks, file)

            # Update the files_tracker
            files_tracker.at[file.Index, "parsed"] = True

        else:
            print(f"The last version of {file.file_name} has already been parsed")

        i += 1
        if max_doc is not None and i >= max_doc:
            break

    pd_chunks.to_csv(pd_chunk_path, index=False)

    files_tracker.to_csv(files_tracker_path, index=False)
    write_AWS(files_tracker_path, files_tracker_path, bucket_block)
    write_AWS(pd_chunk_path, pd_chunk_path, bucket_block)


if __name__ == "__main__":
    max_doc = get_arguments()
    omdena_ungdc_etl_llmsherpa_pdf_parsing_parent(max_doc)

