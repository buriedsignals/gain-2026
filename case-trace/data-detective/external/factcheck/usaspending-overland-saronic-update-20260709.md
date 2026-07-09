# USAspending — DoD prime awards: Overland AI and Saronic Technologies (2022-01-01 to 2026-07-09)
Source: POST https://api.usaspending.gov/api/v2/search/spending_by_award/ (recipient_search_text ["Overland AI"] and ["Saronic"]; award_type_codes A,B,C,D; awarding agency Department of Defense; fields: Award ID, Recipient Name, Award Amount, Start Date, Awarding Agency)
Captured: 2026-07-09

## Query 1: recipient_search_text ["Overland AI"]

```json
{
    "spending_level": "awards",
    "limit": 100,
    "results": [
        {
            "internal_id": 349251868,
            "Award ID": "W911NF25C0004",
            "Recipient Name": "OVERLAND AI INC",
            "Award Amount": 1897682.83,
            "Start Date": "2024-10-25",
            "Awarding Agency": "Department of Defense",
            "awarding_agency_id": 1173,
            "agency_slug": "department-of-defense",
            "generated_internal_id": "CONT_AWD_W911NF25C0004_9700_-NONE-_-NONE-"
        },
        {
            "internal_id": 349251858,
            "Award ID": "W911NF24P0032",
            "Recipient Name": "OVERLAND AI INC",
            "Award Amount": 245696.22,
            "Start Date": "2024-04-15",
            "Awarding Agency": "Department of Defense",
            "awarding_agency_id": 1173,
            "agency_slug": "department-of-defense",
            "generated_internal_id": "CONT_AWD_W911NF24P0032_9700_-NONE-_-NONE-"
        },
        {
            "internal_id": 359787098,
            "Award ID": "W5170126CA063",
            "Recipient Name": "OVERLAND AI INC",
            "Award Amount": 1999989.25,
            "Start Date": "2026-04-15",
            "Awarding Agency": "Department of Defense",
            "awarding_agency_id": 1173,
            "agency_slug": "department-of-defense",
            "generated_internal_id": "CONT_AWD_W5170126CA063_9700_-NONE-_-NONE-"
        },
        {
            "internal_id": 357211324,
            "Award ID": "W5170126CA020",
            "Recipient Name": "OVERLAND AI INC",
            "Award Amount": 1999822.85,
            "Start Date": "2026-01-19",
            "Awarding Agency": "Department of Defense",
            "awarding_agency_id": 1173,
            "agency_slug": "department-of-defense",
            "generated_internal_id": "CONT_AWD_W5170126CA020_9700_-NONE-_-NONE-"
        },
        {
            "internal_id": 352957816,
            "Award ID": "W5170125CA222",
            "Recipient Name": "OVERLAND AI INC",
            "Award Amount": 1999876.04,
            "Start Date": "2025-08-29",
            "Awarding Agency": "Department of Defense",
            "awarding_agency_id": 1173,
            "agency_slug": "department-of-defense",
            "generated_internal_id": "CONT_AWD_W5170125CA222_9700_-NONE-_-NONE-"
        },
        {
            "internal_id": 309319560,
            "Award ID": "M6785425C6532",
            "Recipient Name": "OVERLAND AI INC",
            "Award Amount": 2241642.0,
            "Start Date": "2025-05-16",
            "Awarding Agency": "Department of Defense",
            "awarding_agency_id": 1173,
            "agency_slug": "department-of-defense",
            "generated_internal_id": "CONT_AWD_M6785425C6532_9700_-NONE-_-NONE-"
        },
        {
            "internal_id": 309319064,
            "Award ID": "M6785424C6504",
            "Recipient Name": "OVERLAND AI INC",
            "Award Amount": 226024.0,
            "Start Date": "2023-10-30",
            "Awarding Agency": "Department of Defense",
            "awarding_agency_id": 1173,
            "agency_slug": "department-of-defense",
            "generated_internal_id": "CONT_AWD_M6785424C6504_9700_-NONE-_-NONE-"
        },
        {
            "internal_id": 307305382,
            "Award ID": "HR001123C0159",
            "Recipient Name": "OVERLAND AI INC",
            "Award Amount": 250000.0,
            "Start Date": "2023-09-13",
            "Awarding Agency": "Department of Defense",
            "awarding_agency_id": 1173,
            "agency_slug": "department-of-defense",
            "generated_internal_id": "CONT_AWD_HR001123C0159_9700_-NONE-_-NONE-"
        }
    ],
    "page_metadata": {
        "page": 1,
        "hasNext": false,
        "last_record_unique_id": null,
        "last_record_sort_value": "None"
    },
    "messages": [
        "For searches, time period start and end dates are currently limited to an earliest date of 2007-10-01.  For data going back to 2000-10-01, use either the Custom Award Download feature on the website or one of our download or bulk_download API endpoints as listed on https://api.usaspending.gov/docs/endpoints. "
    ]
}
```

## Query 2: recipient_search_text ["Saronic"]

```json
{
    "spending_level": "awards",
    "limit": 100,
    "results": [
        {
            "internal_id": 355818119,
            "Award ID": "HQ085926FE712",
            "Recipient Name": "SARONIC TECHNOLOGIES, INC",
            "Award Amount": 500.0,
            "Start Date": "2025-12-29",
            "Awarding Agency": "Department of Defense",
            "awarding_agency_id": 1173,
            "agency_slug": "department-of-defense",
            "generated_internal_id": "CONT_AWD_HQ085926FE712_9700_HQ085926DF529_9700"
        }
    ],
    "page_metadata": {
        "page": 1,
        "hasNext": false,
        "last_record_unique_id": null,
        "last_record_sort_value": "None"
    },
    "messages": [
        "For searches, time period start and end dates are currently limited to an earliest date of 2007-10-01.  For data going back to 2000-10-01, use either the Custom Award Download feature on the website or one of our download or bulk_download API endpoints as listed on https://api.usaspending.gov/docs/endpoints. "
    ]
}
```
