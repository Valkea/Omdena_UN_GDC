#! /usr/bin/env python3

"""
PowerBI JSON to CSV Converter

This script provides functions to convert the JSON output of a PowerBI query to a CSV file.

Functions:
- extract: Converts the JSON output to a DataFrame and saves it as a CSV file.
- to_dataframe: Converts the data to a pandas DataFrame.
- reconstruct_arrays: Fixes array index by applying "R" bitset to copy previous values
                     and "Ø" bitset to set null values.
- is_bit_set_for_index: Checks if a bit is set at a given index in the bitset.
- expand_values: Substitutes indexes with actual values.
- replace_newlines_with: Replaces newlines in the data with the specified replacement.

Parameters:
None

Returns:
None
"""

import sys
import csv
import json
from typing import Dict, List, Optional, Any

import pandas as pd


def extract(input_json: Dict[str, Any]) -> pd.DataFrame:
    """
    Converts the JSON output of a PowerBI query to a pandas DataFrame.

    Parameters:
    - input_json (Dict[str, Any]): The JSON input from the PowerBI query.

    Returns:
    pd.DataFrame: The DataFrame representing the converted data.
    """

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


def to_dataframe(columns: List[str], dm0: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Converts the selected data to a pandas DataFrame.

    Parameters:
    - columns (List[str]): The column names.
    - dm0 (List[Dict[str, Any]]): The data.

    Returns:
    pd.DataFrame: The DataFrame representing the data.
    """
    data = pd.DataFrame({}, columns=columns)
    for item in dm0:
        data.loc[len(data)] = item["C"]

    return data


def reconstruct_arrays(
    columns_types: List[Dict[str, Any]], dm0: List[Dict[str, Any]]
) -> None:
    """
    Fixes array index by applying "R" bitset to copy previous values
    and "Ø" bitset to set null values.

    Parameters:
    - columns_types (List[Dict[str, Any]]): The column types.
    - dm0 (List[Dict[str, Any]]): The data.

    Returns:
    None
    """

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


def is_bit_set_for_index(index: int, bitset: int) -> bool:
    """
    Checks if a bit is set at a given index in the bitset.

    Parameters:
    - index (int): The index to check.
    - bitset (int): The bitset.

    Returns:
    bool: True if the bit is set, False otherwise.
    """

    return (bitset >> index) & 1 == 1


def expand_values(
    columns_types: List[Dict[str, Any]],
    dm0: List[Dict[str, Any]],
    value_dicts: Dict[str, List[Optional[str]]],
) -> None:
    """
    Substitutes indexes with actual values.

    Parameters:
    - columns_types (List[Dict[str, Any]]): The column types.
    - dm0 (List[Dict[str, Any]]): The data.
    - value_dicts (Dict[str, List[Optional[str]]]): The value dictionaries.

    Returns:
    None
    """

    for idx, col in enumerate(columns_types):
        if "DN" in col:
            for item in dm0:
                dataItem = item["C"]
                if isinstance(dataItem[idx], int):
                    valDict = value_dicts[col["DN"]]
                    dataItem[idx] = valDict[dataItem[idx]]


def replace_newlines_with(dm0: List[Dict[str, Any]], replacement: str) -> None:
    """
    Replaces newlines in the data with the specified replacement.

    Parameters:
    - dm0 (List[Dict[str, Any]]): The data.
    - replacement (str): The replacement for newlines.

    Returns:
    None
    """

    for item in dm0:
        elem = item["C"]
        for i in range(len(elem)):
            if isinstance(elem[i], str):
                elem[i] = elem[i].replace("\n", replacement)
