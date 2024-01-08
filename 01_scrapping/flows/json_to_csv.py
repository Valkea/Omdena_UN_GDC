import sys
import csv
import json

import pandas as pd


# Converts the JSON output of a PowerBI query to a CSV file
def extract(input_json, output_file):

    data = input_json["results"][0]["result"]["data"]
    dm0 = data["dsr"]["DS"][0]["PH"][0]["DM0"]
    columns_types = dm0[0]["S"]
    columns = [
        item["GroupKeys"][0]["Source"]["Property"]
        for item in data["descriptor"]["Select"]
        if item["Kind"] == 1
    ]
    rest_columns = [
        item["Value"] for item in data["descriptor"]["Select"] if item["Kind"] == 2
    ]
    for col in rest_columns:
        columns.append(col)
    value_dicts = data["dsr"]["DS"][0].get("ValueDicts", {})

    reconstruct_arrays(columns_types, dm0)
    expand_values(columns_types, dm0, value_dicts)

    replace_newlines_with(dm0, "")
    return to_dataframe(columns, dm0)


def to_dataframe(columns, dm0):

    data = pd.DataFrame({}, columns=columns)
    for item in dm0:
        data.loc[len(data)] = item['C']

    return data


def reconstruct_arrays(columns_types, dm0):
    # fixes array index by applying
    # "R" bitset to copy previous values
    # "Ø" bitset to set null values
    lenght = len(columns_types)
    for item in dm0:
        currentItem = item["C"]
        if "R" in item or "Ø" in item:
            copyBitset = item.get("R", 0)
            deleteBitSet = item.get("Ø", 0)
            for i in range(lenght):
                if is_bit_set_for_index(i, copyBitset):
                    currentItem.insert(i, prevItem[i])
                elif is_bit_set_for_index(i, deleteBitSet):
                    currentItem.insert(i, None)
        prevItem = currentItem


def is_bit_set_for_index(index, bitset):
    return (bitset >> index) & 1 == 1


# substitute indexes with actual values
def expand_values(columns_types, dm0, value_dicts):
    for idx, col in enumerate(columns_types):
        if "DN" in col:
            for item in dm0:
                dataItem = item["C"]
                if isinstance(dataItem[idx], int):
                    valDict = value_dicts[col["DN"]]
                    dataItem[idx] = valDict[dataItem[idx]]


def replace_newlines_with(dm0, replacement):
    for item in dm0:
        elem = item["C"]
        for i in range(len(elem)):
            if isinstance(elem[i], str):
                elem[i] = elem[i].replace("\n", replacement)
