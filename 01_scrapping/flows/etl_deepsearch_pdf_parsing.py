import os
import json
import zipfile
from pathlib import Path

import pandas as pd

import deepsearch as ds
from deepsearch.cps.client.api import CpsApi

from prefect import flow, task
from prefect_aws import S3Bucket

from etl_common import read_AWS, write_AWS


@task(name="Parse PDF", log_prints=True)
def parse_PDF(api, proj_key, local_dir, file_path, file_infos):
    print(f"ETL | PDF parsing | Task: DeepSearch with {file_path}")

    documents = ds.convert_documents(api=api, proj_key=proj_key, source_path=file_path)
    documents.download_all(result_dir=local_dir)


@task(name="Extract JSON from ZIP", log_prints=True)
def extract_json(result_dir):
    print("ETL | PDF parsing | Task: Extracting JSON from Zip")

    json_file_path = None
    print("Extract from", result_dir)
    for document in os.listdir(result_dir):
        if document.endswith(".zip"):
            print(document)

            zip_file_path = Path(result_dir, document)
            with zipfile.ZipFile(zip_file_path, "r") as z:
                for filename in z.namelist():
                    if filename.endswith(".json"):
                        print(filename)

                        with z.open(filename) as f:
                            data = json.loads(f.read().decode("utf-8"))

                            json_file_path = Path(result_dir, filename)
                            with open(json_file_path, "w") as f:
                                json.dump(data, f, indent=4)

            os.remove(zip_file_path)

    return json_file_path


@task(name="Parse JSON", log_prints=True)
def parse_JSON(file_path):
    print(f"ETL | PDF parsing | Task: Extracting infos from JSON {file_path}")


@flow(log_prints=True)
def omdena_ungdc_etl_pdf_parsing_parent() -> None:
    print("ETL | PDF parsing")

    # Define IBM DeepSearch access
    api = CpsApi.from_env()
    proj_key = api.projects.list()[0].key

    # Get the list of files to ingest
    bucket_block = S3Bucket.load("omdena-un-gdc-bucket")

    local_dir = "data"
    if not os.path.exists(local_dir):
        raise Exception("The source folder doesn't exist")

    files_tracker_path = Path(local_dir, "files_tracker.csv")
    read_AWS(files_tracker_path, files_tracker_path, bucket_block)
    files_tracker = pd.read_csv(files_tracker_path)

    # Parse the collected files
    for file in files_tracker.itertuples():
        if file.present_in_last_update is True and file.parsed is False:
            file_path = Path(local_dir, file.file_name)

            # Parse PDF using IBM DeepSearch
            parse_PDF(api, proj_key, local_dir, file_path, file)

            # Extract the JSON file from the returned DeepSearch Zip
            json_file_path = extract_json(local_dir)

            # Extract interesting information from JSON file
            parse_JSON(json_file_path)

            # Update the files_tracker
            files_tracker.at[file.Index, 'parsed'] = True
        else:
            print(f"The last version of {file.file_name} has already been parsed")

    files_tracker.to_csv(files_tracker_path, index=False)
    write_AWS(files_tracker_path, files_tracker_path, bucket_block)


if __name__ == "__main__":
    omdena_ungdc_etl_pdf_parsing_parent()

##########################################

# def docs_to_json(path_to_docs: str, save_json:bool, result_dir:str) -> list[dict]:
#     """
#         pass one document or a folder of documents to deepsearch for parsing. The result is a list of jsons(dicts)
#         :param str path_to_docs: path to the document or folder of documents
#         :param bool save_json: if True, saves jsons to the result_dir
#         :param str result_dir: path to the folder where the results will be saved (zip files and jsons)
#     """
#
#     print("send documents")
#     documents = ds.convert_documents(api=api,proj_key=proj_key, source_path=path_to_docs)
#     print("parse results")
#     documents.download_all(result_dir = result_dir)
#
#     for document in os.listdir(result_dir):
#         if document.endswith(".zip"):
#             print(document)
#             with zipfile.ZipFile(os.path.join(result_dir, document), 'r') as z:
#                 for filename in z.namelist():
#                     if filename.endswith(".json"):
#                         print(filename)
#                         with z.open(filename) as f:
#                             data = json.loads(f.read().decode("utf-8"))
#                             if save_json:
#                                 with open(os.path.join(result_dir, filename), "w") as f:
#                                     json.dump(data, f, indent=4)
#
#
# if __name__ == "__main__":
#
#     # you need to get an api key and configure your profile before.
#     api = CpsApi.from_env()
#
#     # assumes that you only have one project, otherwise you need to specify the project key
#     proj_key = api.projects.list()[0].key
#     print("proj_key:", proj_key)
#
#     result_dir = "./results/"
#     save_json = True
#
#     # in docs folder I have 'GDC-submission_Amazon.pdf' and 'GDC-submission_Japan.pdf'
#     path_to_docs = "./data/src/"
#
#     documents = docs_to_json(path_to_docs=path_to_docs, save_json=save_json, result_dir=result_dir)
#
#
