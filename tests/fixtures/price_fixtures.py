JSON_STRING_FIXTURE = """{
    "timestamp": "2023-05-06 18:25",
    "api_response": "{'data': {'viewer': {'homes': [{'currentSubscription': {'priceInfo': {'today': [{'total': 0.9058}, {'total': 0.8753}, {'total': 0.9336}, {'total': 0.944}, {'total': 0.9764}, {'total': -0.2852}, {'total': -0.3604}, {'total': 1.0013}, {'total': 1.0195}, {'total': 1.0348}, {'total': 0.9536}, {'total': 0.8753}, {'total': 0.8474}, {'total': 0.7843}, {'total': 0.778}, {'total': 0.7775}, {'total': 0.878}, {'total': 0.9906}, {'total': 1.0392}, {'total': 1.068}, {'total': 1.086}, {'total': 1.1052}, {'total': 1.0873}, {'total': 1.0464}], 'tomorrow': [{'total': 1.0453}, {'total': 0.9722}, {'total': 0.9624}, {'total': 0.9723}, {'total': 0.9656}, {'total': 0.9788}, {'total': 0.968}, {'total': 0.9532}, {'total': 0.9049}, {'total': 0.814}, {'total': 0.7357}, {'total': 0.7482}, {'total': 0.7385}, {'total': 0.7148}, {'total': 0.6499}, {'total': 0.6393}, {'total': 0.6804}, {'total': 0.928}, {'total': 1.0619}, {'total': 1.1052}, {'total': 1.1064}, {'total': 1.1072}, {'total': 1.0864}, {'total': 1.0745}]}}}]}}}"
}"""

FIXTURE_API_RESPONSE = {
    "data": {
        "viewer": {
            "homes": [
                {
                    "currentSubscription": {
                        "priceInfo": {
                            "today": [
                                {"total": 0.313},
                                {"total": 0.2938},
                                {"total": 0.2796},
                                {"total": 0.2578},
                                {"total": 0.2574},
                                {"total": 0.224},
                                {"total": 0.2004},
                                {"total": 0.2586},
                                {"total": 0.2972},
                                {"total": 0.3126},
                                {"total": 0.3199},
                                {"total": 0.3208},
                                {"total": 0.2878},
                                {"total": 0.3178},
                                {"total": 0.3215},
                                {"total": 0.3263},
                                {"total": 0.3607},
                                {"total": 1.6412},
                                {"total": 1.8496},
                                {"total": 1.9834},
                                {"total": 1.9244},
                                {"total": 1.9545},
                                {"total": 0.4532},
                                {"total": 0.4293},
                            ],
                            "tomorrow": [
                                {"total": 0.4678},
                                {"total": 0.4601},
                                {"total": 0.4712},
                                {"total": 0.4859},
                                {"total": 0.5428},
                                {"total": 1.4626},
                                {"total": 1.762},
                                {"total": 2.1994},
                                {"total": 2.2762},
                                {"total": 1.9614},
                                {"total": 1.8425},
                                {"total": 1.8168},
                                {"total": 1.6708},
                                {"total": 1.5989},
                                {"total": 1.5681},
                                {"total": 1.8154},
                                {"total": 1.8409},
                                {"total": 2.3418},
                                {"total": 2.5326},
                                {"total": 2.7132},
                                {"total": 2.5905},
                                {"total": 2.1766},
                                {"total": 0.6994},
                                {"total": 0.5146},
                            ],
                        }
                    }
                }
            ]
        }
    }
}


FIXTURE_TODAY_PRICES = [
    0.313,
    0.2938,
    0.2796,
    0.2578,
    0.2574,
    0.224,
    0.2004,
    0.2586,
    0.2972,
    0.3126,
    0.3199,
    0.3208,
    0.2878,
    0.3178,
    0.3215,
    0.3263,
    0.3607,
    1.6412,
    1.8496,
    1.9834,
    1.9244,
    1.9545,
    0.4532,
    0.4293,
]

# json_loaded_fixture = json.loads(json_string_fixture)
