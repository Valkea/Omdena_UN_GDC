####################
# Author : Kulwinder K.
# Date : 12/12/2023
# This script scrapes the Power BI dashboard from the below website
# https://www.un.org/techenvoy/global-digital-compact
# and gives back the CSV file
# It calls json_to_csv.py file inside the script.
####################
# Co-Author : Emmanuel Letremble
# Date : 08/01/2024
# Improved the script to run in less than 1 min instead of about 1H
#####################

import requests
import pandas as pd

from prefect import flow, task

from json_to_csv import extract


@task(name="Scrap page 1", log_prints=True)
def page_1_scraping(api_url, payload, headers):
    print(">>> MAIN TABLE")
    table_data = requests.post(api_url, json=payload, headers=headers).json()
    return extract(table_data, "output_file.csv")


@task(name="Scrap page 2", log_prints=True)
def page_2_scraping(api_url, payload_p2, headers, df):
    """
    Input Parameters - query_payload to retrieve the Core Principles
                     - dataframe df
                     - API URL
                     - Headers

    Retuns - df with addition of new columns scarped
    """

    # SET TOPICS
    # Topic names are manually added from the Page 2 of Power BI
    # It would be better if this is also automated to make it more agile.
    topics = [
        "Accountability for Discrimination/Misleading Content",
        "Connect all People",
        "Digital Commons",
        "Human Rights Online",
        "Internet Fragmentation",
        "Other Area",
        "Protect Data",
        "Regulation of AI",
    ]

    # POPULATE TOPICS
    for topic in topics:
        print(">>> TOPIC:", topic)
        clean_topic = topic.replace(" ", "_").replace("/", "_")

        payload_p2["queries"][0]["Query"]["Commands"]\
                [0]["SemanticQueryDataShapeCommand"]["Query"]\
                ["Where"][0]["Condition"]["In"]["Values"]\
                [0][0]["Literal"]["Value"] = f"'{topic}'"

        result = requests.post(api_url, json=payload_p2, headers=headers).json()
        query_df = extract(result, f"output_file_{topic[:10]}.csv")

        # Merge the `Core Principles` and `Commitments, pledges or actions` columns with the existing DF
        cols = ["Record ID", "Core Principles", "Commitments, pledges or actions"]
        tmp_df = query_df.loc[ :, cols ]
        tmp_df.rename(
            columns={
                "Core Principles": f"Core_Principle__{clean_topic}",
                "Commitments, pledges or actions": f"Commitments_pledges_or_actions__{clean_topic}"
            }, inplace=True
        )

        left = df.set_index("Record ID", drop=False)
        right = tmp_df.set_index("Record ID", drop=True)
        df = left.join(right, how="left", lsuffix="", rsuffix=f"__{clean_topic}")

    else:

        print(">>> PROCESS DESCRIPTION")
        # Merge the `Process description` column on the last call
        left = df.set_index("Record ID", drop=False)

        tmp_df = query_df.loc[:, ["Record ID", "Process description"]]
        right = tmp_df.set_index("Record ID", drop=True)

        df = left.join(right, how="left", lsuffix="", rsuffix=f"")

    return df


@flow(log_prints=True)
def omdena_ungdc_etl_scrap_pbi_parent() -> None:

    # payload for tables and second page sections
    payload_p1 = {
        "version": "1.0.0",
        "queries": [
            {
                "Query": {
                    "Commands": [
                        {
                            "SemanticQueryDataShapeCommand": {
                                "Query": {
                                    "Version": 2,
                                    "From": [
                                        {
                                            "Name": "d",
                                            "Entity": "Demographics",
                                            "Type": 0,
                                        },
                                        {
                                            "Name": "a",
                                            "Entity": "All Areas combined",
                                            "Type": 0,
                                        },
                                    ],
                                    "Select": [
                                        {
                                            "Column": {
                                                "Expression": {
                                                    "SourceRef": {"Source": "d"}
                                                },
                                                "Property": "Type",
                                            },
                                            "Name": "Demographics.Type",
                                        },
                                        {
                                            "Column": {
                                                "Expression": {
                                                    "SourceRef": {"Source": "d"}
                                                },
                                                "Property": "Location formatted",
                                            },
                                            "Name": "Demographics.Location formatted",
                                        },
                                        {
                                            "Column": {
                                                "Expression": {
                                                    "SourceRef": {"Source": "d"}
                                                },
                                                "Property": "Contact Name",
                                            },
                                            "Name": "Demographics.Contact Name",
                                        },
                                        {
                                            "Column": {
                                                "Expression": {
                                                    "SourceRef": {"Source": "d"}
                                                },
                                                "Property": "Entity Name",
                                            },
                                            "Name": "Demographics.Entity Name",
                                        },
                                        {
                                            "Column": {
                                                "Expression": {
                                                    "SourceRef": {"Source": "a"}
                                                },
                                                "Property": "Record ID",
                                            },
                                            "Name": "All Areas combined.Record ID",
                                            "NativeReferenceName": "Record ID1",
                                        },
                                    ],
                                    "Where": [
                                        {
                                            "Condition": {
                                                "In": {
                                                    "Expressions": [
                                                        {
                                                            "Column": {
                                                                "Expression": {
                                                                    "SourceRef": {
                                                                        "Source": "a"
                                                                    }
                                                                },
                                                                "Property": "Area",
                                                            }
                                                        }
                                                    ],
                                                    "Values": [
                                                        [
                                                            {
                                                                "Literal": {
                                                                    "Value": "'Connect all People'"
                                                                }
                                                            }
                                                        ],
                                                        [
                                                            {
                                                                "Literal": {
                                                                    "Value": "'Accountability for Discrimination/Misleading Content'"
                                                                }
                                                            }
                                                        ],
                                                        [
                                                            {
                                                                "Literal": {
                                                                    "Value": "'Digital Commons'"
                                                                }
                                                            }
                                                        ],
                                                        [
                                                            {
                                                                "Literal": {
                                                                    "Value": "'Regulation of AI'"
                                                                }
                                                            }
                                                        ],
                                                        [
                                                            {
                                                                "Literal": {
                                                                    "Value": "'Protect Data'"
                                                                }
                                                            }
                                                        ],
                                                        [
                                                            {
                                                                "Literal": {
                                                                    "Value": "'Internet Fragmentation'"
                                                                }
                                                            }
                                                        ],
                                                        [
                                                            {
                                                                "Literal": {
                                                                    "Value": "'Human Rights Online'"
                                                                }
                                                            }
                                                        ],
                                                        [
                                                            {
                                                                "Literal": {
                                                                    "Value": "'Other Area'"
                                                                }
                                                            }
                                                        ],
                                                    ],
                                                }
                                            }
                                        }
                                    ],
                                    "OrderBy": [
                                        {
                                            "Direction": 2,
                                            "Expression": {
                                                "Aggregation": {
                                                    "Expression": {
                                                        "Column": {
                                                            "Expression": {
                                                                "SourceRef": {
                                                                    "Source": "a"
                                                                }
                                                            },
                                                            "Property": "Core Principles",
                                                        }
                                                    },
                                                    "Function": 2,
                                                }
                                            },
                                        }
                                    ],
                                },
                                "Binding": {
                                    "Primary": {
                                        "Groupings": [
                                            {"Projections": [0, 1, 2, 3, 4]}
                                        ]
                                    },
                                    "DataReduction": {
                                        "DataVolume": 3,
                                        "Primary": {"Window": {"Count": 500}},
                                    },
                                    "Version": 1,
                                },
                                "ExecutionMetricsKind": 1,
                            }
                        }
                    ]
                },
                "CacheKey": "",
                "QueryId": "",
                "ApplicationContext": {
                    "DatasetId": "fb1276c8-e98e-4b26-a7d3-24a40ae84000",
                    "Sources": [
                        {
                            "ReportId": "a70c1024-15f3-4f74-aa2e-2f1897acfdb6",
                            "VisualId": "fc23d492ddbe07d7e1a4",
                        }
                    ],
                },
            }
        ],
        "cancelQueries": [],
        "modelId": 933989,
    }

    payload_p2 = {
        "version": "1.0.0",
        "queries": [
            {
                "Query": {
                    "Commands": [
                        {
                            "SemanticQueryDataShapeCommand": {
                                "Query": {
                                    "Version": 2,
                                    "From": [
                                        {
                                            "Name": "a",
                                            "Entity": "All Areas combined",
                                            "Type": 0,
                                        },
                                        {
                                            "Name": "b",
                                            "Entity": "Demographics",
                                            "Type": 0,
                                        },
                                    ],
                                    "Select": [
                                        {
                                            "Column": {
                                                "Expression": {
                                                    "SourceRef": {"Source": "a"}
                                                },
                                                "Property": "Record ID",
                                            },
                                            "Name": "Record ID",
                                        },
                                        {
                                            "Column": {
                                                "Expression": {
                                                    "SourceRef": {"Source": "a"}
                                                },
                                                "Property": "Core Principles",
                                            },
                                            "Name": "All Areas combined.Core Principles",
                                        },
                                        {
                                            "Column": {
                                                "Expression": {
                                                    "SourceRef": {"Source": "a"}
                                                },
                                                "Property": "Commitments, pledges or actions",
                                            },
                                            "Name": "All Areas combined.Commitments, pledges or actions",
                                        },
                                        {
                                            "Column": {
                                                "Expression": {
                                                    "SourceRef": {"Source": "b"}
                                                },
                                                "Property": "Process description",
                                            },
                                            "Name": "Demographics.Process description",
                                        },
                                    ],
                                    "OrderBy": [
                                        {
                                            "Direction": 2,
                                            "Expression": {
                                                "Column": {
                                                    "Expression": {
                                                        "SourceRef": {"Source": "a"}
                                                    },
                                                    "Property": "Core Principles",
                                                    # "Property": "Record ID",
                                                    # "Property": "Area",
                                                }
                                            },
                                        }
                                    ],
                                    "Where": [
                                        {
                                            "Condition": {
                                                "In": {
                                                    "Expressions": [
                                                        {
                                                            "Column": {
                                                                "Expression": {
                                                                    "SourceRef": {
                                                                        "Source": "a"
                                                                    }
                                                                },
                                                                "Property": "Area",
                                                            }
                                                        }
                                                    ],
                                                    "Values": [
                                                        [
                                                            {
                                                                "Literal": {
                                                                    "Value": "'Accountability for Discrimination/Misleading Content'"
                                                                }
                                                            }
                                                        ],
                                                    ],
                                                }
                                            }
                                        },
                                        {
                                            "Condition": {
                                                "In": {
                                                    "Expressions": [
                                                        {
                                                            "Column": {
                                                                "Expression": {
                                                                    "SourceRef": {
                                                                        "Source": "a"
                                                                    }
                                                                },
                                                                "Property": "Record ID",
                                                            }
                                                        }
                                                    ],
                                                    "Values": [
                                                        [
                                                            {
                                                                "Literal": {
                                                                    "Value": "'638159590404564717'"
                                                                }
                                                            },
                                                        ],
                                                        [
                                                            {
                                                                "Literal": {
                                                                    "Value": "'638183478316757857'"
                                                                }
                                                            },
                                                        ],
                                                    ],
                                                }
                                            }
                                        },
                                    ],
                                },
                                "Binding": {
                                    "Primary": {
                                        "Groupings": [{"Projections": [0, 1, 2, 3]}]
                                    },
                                    # "Primary": {"Groupings": [{"Projections": [0]}]},
                                    "DataReduction": {
                                        "DataVolume": 3,
                                        "Primary": {"Top": {}},
                                        # "Primary": {"Window": {"Count": 500}},
                                    },
                                    "Version": 1,
                                },
                                "ExecutionMetricsKind": 1,
                            }
                        }
                    ]
                },
                "CacheKey": "",
                "QueryId": "",
                "ApplicationContext": {
                    "DatasetId": "fb1276c8-e98e-4b26-a7d3-24a40ae84000",
                    "Sources": [
                        {
                            "ReportId": "a70c1024-15f3-4f74-aa2e-2f1897acfdb6",
                            "VisualId": "58d5b49030dc6e9c802b",
                        }
                    ],
                },
            }
        ],
        "cancelQueries": [],
        "modelId": 933989,
    }

    # api url copied form the Headers section of Network>XHR
    api_url = "https://wabi-north-europe-j-primary-api.analysis.windows.net/public/reports/querydata?synchronous=true"
    headers = {
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "X-Powerbi-Resourcekey": "84db278f-178b-4a18-a0db-3e57e8113b1f",
    }

    ##### START SCRAPING P1 #####

    df = page_1_scraping(api_url, payload_p1, headers)

    ##### SET RECORD IDS #####

    record_id = df["Record ID"].tolist()
    ids = [
        [
            {"Literal": {"Value": f"'{x}'"}},
        ]
        for x in record_id
    ]
    payload_p2["queries"][0]["Query"]["Commands"][0][
        "SemanticQueryDataShapeCommand"
    ]["Query"]["Where"][1]["Condition"]["In"]["Values"] = ids

    ##### START SCRAPING P2 #####

    df = page_2_scraping(api_url, payload_p2, headers, df)
    df.to_csv("df.csv", index=False)

    print("Scrapping completed")


if __name__ == "__main__":
    omdena_ungdc_etl_scrap_pbi_parent()
