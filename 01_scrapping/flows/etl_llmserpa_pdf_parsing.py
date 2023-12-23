#! /usr/bin/env python3

import pathlib

import pandas as pd

# from PyPDF2 import PdfReader
from llmsherpa.readers import LayoutPDFReader

# from llama_index import VectorStoreIndex

from prefect import flow, task
from prefect_aws import S3Bucket

from etl_common import read_AWS

@task(
    name="Parse PDF",
    log_prints=True,
)
def parse_PDF(file_path, file_infos):

    # storage_context_backup_path = pathlib.Path('data', 'VectoreStoreIndex_StorageContext')

    # --- PREPARE PDF PARSER

    llmsherpa_api_url = "https://readers.llmsherpa.com/api/document/developer/parseDocument?renderFormat=all"
    pdf_reader = LayoutPDFReader(llmsherpa_api_url)

    # --- PARSE PDF

    file_path = pathlib.Path("/home/valkea/Dev/Projets_Benevoles/Omdena_UN_Global_Digital_Compact/Github/01_scrapping", file_path)
    print("file_path:", file_path)
    doc = pdf_reader.read_pdf(str(file_path))

    # --- PREPARE NODES

    print("\n", " DOCUMENTS ".center(100, "*"))
    # index = VectorStoreIndex([])


    columns = ['file_hash','file_name','chunk']
    pdf_chunks = pd.DataFrame(columns=columns)
    
    for chunk in doc.chunks():
        print(f"\nDOCUMENT >>> {chunk.to_context_text()}")
        # index.insert(Document(text=chunk.to_context_text(), extra_info={}))
        new_row = {"file_hash": file_infos.file_hash, "file_name": file_infos.file_name, "chunk": chunk.to_context_text()}
        pdf_chunks = pd.concat([pdf_chunks, pd.DataFrame([new_row])], ignore_index=True)

    for section in doc.sections():
        print(f"\nDOCUMENT >>> {section.title}")
        new_row = {"file_hash": file_infos.file_hash, "file_name": file_infos.file_name, "chunk": section.title}
        pdf_chunks = pd.concat([pdf_chunks, pd.DataFrame([new_row])], ignore_index=True)

    pdf_chunks.to_csv(pathlib.Path("data", f"{file_infos.file_name}.csv"))

    # --- SAVE VECTOR STORE

    # index.storage_context.persist(storage_context_backup_path)


@flow(log_prints=True)
def omdena_ungdc_etl_pdf_parsing_parent() -> None:

    print("ETL | PDF parsing")

    bucket_block = S3Bucket.load("omdena-un-gdc-bucket")

    files_tracker_path = pathlib.Path('data', 'files_tracker.csv')
    read_AWS(files_tracker_path, files_tracker_path, bucket_block)

    files_tracker = pd.read_csv(files_tracker_path)

    for file in files_tracker.itertuples():
        print("===>", file)
        if file.present_in_last_update is True:
            file_path = pathlib.Path('data', file.file_name)
            print("OUIIIIIII", file_path)
            parse_PDF(file_path, file)





if __name__ == "__main__":
    omdena_ungdc_etl_pdf_parsing_parent()
