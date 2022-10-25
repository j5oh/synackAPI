### /v2/ endpoint
#### This is the return JSON:
```
[
    {
        "id":STRING,
        "title":STRING,
        "description":STRING,
        "taskTemplateUid":STRING,
        "taskTemplateCredits":INT,
        "campaignUid":STRING,
        "campaignName":STRING,
        "listingUid":STRING,
        "listingCodename":STRING,
        "organizationUid":STRING
        "organizationCodename":STRING,
        "status":STRING,
        "hasBeenViewed":BOOL,
        "payout":{
            "amount":INT,
            "currency":STRING
        },
        "credits":INT,
        "assetTypes":[STRING],
        "categories":[STRING],
        "taskType":STRING,
        "batchId":STRING,
        "definitionId":STRING,
        "taskGroup":STRING,
        "scope":STRING,
        "response":STRING,
        "structuredResponse":STRING,
        "responseType":STRING,
        "assignee":STRING,
        "reviewer":STRING,
        "position":INT,
        "createdOn":STRING(datetime format),
        "createdBy":STRING,
        "modifiedOn":STRING(datetime format),
        "modifiedBy":STRING,
        "maxCompletionTimeInSecs":INT,
        "pausedDurationInSecs":INT,
        "version":STRING,
        "validResponses":[
            {
                "label":STRING,
                "value":STRING
            },
            {
                "label":STRING,
                "value":STRING
            },
            {
                "label":STRING,
                "value":STRING
            }
        ],
        "publishedOn":STRING(datetime format),
        "deactivatedOn":null,
        "canEditResponse":BOOL,
        "isAssigneeCurrentUser":BOOL,
        "controlFamily":STRING,
        "fismaLow":STRING,
        "fismaModerate":STRING,
        "fismaHigh":STRING
    }
]
```

### /v1/ endpoint
#### This is what is used to claim:

```
POST /api/tasks/v1/organizations/[organizationUid]/listings/[listingUid]/campaigns/[campaignUid]/tasks/[id]/transitions HTTP/1.1

{
  "type":"CLAIM"
}
```
