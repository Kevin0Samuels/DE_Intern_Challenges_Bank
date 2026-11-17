# Data Profiling Report: Springer Capital Referral System

This report provides a systematic statistical and schema profiling of all 7 source tables.

## 1. Tables Overview

| Table Name | File Name | Total Rows | Total Columns | Total Null Cells |
| --- | --- | --- | --- | --- |
| user_referrals | user_referrals.csv | 46 | 11 | 70 |
| user_referral_logs | user_referral_logs.csv | 96 | 5 | 79 |
| user_logs | user_logs.csv | 29 | 8 | 0 |
| user_referral_statuses | user_referral_statuses.csv | 3 | 3 | 0 |
| referral_rewards | referral_rewards.csv | 3 | 4 | 0 |
| paid_transactions | paid_transactions.csv | 14 | 6 | 0 |
| lead_log | lead_log.csv | 8 | 7 | 0 |

---

## 2. Table: `user_referrals`

| Column Name | Data Type | Defined Length | Nulls Allowed | Null Count | % Populated | Distinct Value Count | Minimum Value | Maximum Value | Max Actual Length | Top Frequencies | Detected Pattern |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| referral_at | TIMESTAMP | 24 | No | 0 | 100.00% | 44 | 2024-03-08T11:31:24Z | 2024-05-24T04:57:33Z | 20 | '2024-04-22T15:04:57Z': 2, '2024-04-23T04:55:40Z': 2, '2024-05-01T05:17:31Z': 1 | ISO8601 Timestamp |
| referral_id | VARCHAR | 32 | No | 0 | 100.00% | 46 | 1f44ffca9257eefe62892409bce4b704 | fcb804c8ff24e5b2974a7e965ebea5e8 | 32 | '9331c8f144dad5a3b8e4a10467b4343a': 1, '636f4143f3bbe2a832d3f8e3c7b7d848': 1, '30a0cdbe9f518b9938bf9b9399f8b048': 1 | Hex32 (MD5/UUID Hash) |
| referee_id | VARCHAR | 32 | Yes | 3 | 93.48% | 37 | 04aec3adea13099cb24c4cc784f05f3d | f6507a982bde1dcda0ce0867ceac66f6 | 32 | '08b8ab0371b6a0cb79319628505c446c': 4, '12dd343d282fb7915f55982937c30b87': 3, 'c6fb4aa67eba0ed851ac4182abe26127': 2 | Hex32 (MD5/UUID Hash) |
| referee_name | VARCHAR | 64 | Yes | 3 | 93.48% | 35 | 069396bf68713451107ed621971b8fd3 | feb4d885f99957d87b2e8eb1fd05b193 | 32 | '8ef43a9189c084778dadf266d6ee6071': 3, '4f5649d2d7b3ee9406436f026094c1fe': 3, '360701f01f783634925ce89e59decc37': 3 | Hex32 (MD5/UUID Hash) |
| referee_phone | VARCHAR | 32 | Yes | 0 | 100.00% | 33 | 0520c1cc85cbd43be086d6067e316e39 | ff6a10e68ce4c4a56e3c19238619f828 | 32 | 'ce52ad7070f305b43a784b8503dbde13': 10, 'c72ff35974713260b8153d81c84b3fa5': 3, '5ba638fed7578e677c7600f1038f1b77': 3 | Hex32 (MD5/UUID Hash) |
| referral_reward_id | INTEGER | 10 | Yes | 38 | 17.39% | 3 | 1 | 3 | 1 | '1': 5, '2': 2, '3': 1 | Numeric Integer |
| referral_source | VARCHAR | 32 | No | 0 | 100.00% | 3 | Draft Transaction | User Sign Up | 17 | 'Draft Transaction': 27, 'Lead': 11, 'User Sign Up': 8 | Text / String |
| referrer_id | VARCHAR | 32 | Yes | 13 | 71.74% | 13 | 192befbbd8b97260e28db080a661578c | f2de40c8394f4ea9a6aa49965380dd8f | 32 | '2c71c5d66c7e12a0b3c200ba6ed3b78e': 13, '4acfa96cb521b6963b50bcef95bee485': 7, 'f2de40c8394f4ea9a6aa49965380dd8f': 2 | Hex32 (MD5/UUID Hash) |
| transaction_id | VARCHAR | 32 | Yes | 13 | 71.74% | 27 | 07f21743663aacb7d212c286d47a14de | f192fca27d438c053db425fade152d66 | 32 | '4c8cae052f19cea66544affc759b76ee': 4, 'da0071e2bb7794ac19ff4dbbb6e772f0': 3, '7709d17eaec03665f58904b72c8ab444': 2 | Hex32 (MD5/UUID Hash) |
| updated_at | TIMESTAMP | 24 | No | 0 | 100.00% | 40 | 2024-04-29T04:04:15Z | 2024-05-24T04:57:33Z | 20 | '2024-05-01T02:58:58Z': 4, '2024-05-01T02:58:57Z': 3, '2024-05-23T05:32:21Z': 2 | ISO8601 Timestamp |
| user_referral_status_id | INTEGER | 10 | No | 0 | 100.00% | 3 | 1 | 3 | Not a string | '1': 29, '3': 9, '2': 8 | Numeric Integer |

## 2. Table: `user_referral_logs`

| Column Name | Data Type | Defined Length | Nulls Allowed | Null Count | % Populated | Distinct Value Count | Minimum Value | Maximum Value | Max Actual Length | Top Frequencies | Detected Pattern |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| id | INTEGER | 10 | No | 0 | 100.00% | 96 | 1 | 96 | Not a string | '1': 1, '2': 1, '71': 1 | Numeric Integer |
| user_referral_id | VARCHAR | 32 | No | 0 | 100.00% | 78 | 119330b602a0e3bc0b66487b6c53ec19 | ffea2078bee21f79f199256757e5d578 | 32 | '7a03e01e0c17b2322845242a796adb5e': 19, '433df86639089a01ce358b27aebdf19f': 1, '86613e057860f1d6bb6d50986d513794': 1 | Hex32 (MD5/UUID Hash) |
| source_transaction_id | VARCHAR | 32 | Yes | 79 | 17.71% | 17 | 0d5745a60be9f0d9163c99c91fd61efc | de0d476b360046c0d079d5f8fcb77c00 | 32 | 'aa7f55497ab7a5842145c6c58e1395c2': 1, '1a38a3d929b892b855a5aebab3a7da0b': 1, 'd4b50fe31e2f0143ac639aeaeb4b3820': 1 | Hex32 (MD5/UUID Hash) |
| created_at | TIMESTAMP | 24 | No | 0 | 100.00% | 96 | 2024-03-08T11:33:50Z | 2024-07-10T08:51:11Z | 20 | '2024-06-02T20:42:09Z': 1, '2024-06-25T07:57:00Z': 1, '2024-06-04T08:04:16Z': 1 | ISO8601 Timestamp |
| is_reward_granted | BOOLEAN | 1 | No | 0 | 100.00% | 2 | False | True | Not a string | 'False': 79, 'True': 17 | Boolean Flag |

## 2. Table: `user_logs`

| Column Name | Data Type | Defined Length | Nulls Allowed | Null Count | % Populated | Distinct Value Count | Minimum Value | Maximum Value | Max Actual Length | Top Frequencies | Detected Pattern |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| id | INTEGER | 10 | No | 0 | 100.00% | 29 | 1 | 29 | Not a string | '1': 1, '16': 1, '28': 1 | Numeric Integer |
| user_id | VARCHAR | 32 | No | 0 | 100.00% | 9 | 192befbbd8b97260e28db080a661578c | f2de40c8394f4ea9a6aa49965380dd8f | 32 | '2c71c5d66c7e12a0b3c200ba6ed3b78e': 13, '4acfa96cb521b6963b50bcef95bee485': 7, 'cadba628952bde1670ac4c0792afc28a': 2 | Hex32 (MD5/UUID Hash) |
| name | VARCHAR | 64 | Yes | 0 | 100.00% | 7 | 003609f9b658dc89cd16d904783834d4 | ec55b0c6b4cf5e7e08ddcfbc0465b796 | 32 | '6380232145160dca709cdb11ae47fb2a': 13, 'a2d59a13f5f24ae696b0c6917f86a82f': 7, '2eb4b6e1ee9574c9e4a5f7e7e9b09280': 5 | Hex32 (MD5/UUID Hash) |
| phone_number | VARCHAR | 32 | Yes | 0 | 100.00% | 9 | 488b1d38c3a3d84ab9839886acecf5e0 | f495c5b0268d9896b8478ab32bfa02eb | 32 | '87e6571bf783832fffc616a308563e7e': 13, 'de389f61ac5c8c7ec16ca07369048d0e': 7, '6f1afb7c23074684ea05ffe9e63bb57a': 2 | Hex32 (MD5/UUID Hash) |
| homeclub | VARCHAR | 50 | Yes | 0 | 100.00% | 6 | ADITYAWARMAN | SUNSET ROAD | 19 | 'BENHIL': 14, 'BLOK M': 7, 'PLUIT': 5 | Text / String |
| timezone_homeclub | VARCHAR | 30 | Yes | 0 | 100.00% | 2 | Asia/Jakarta | Asia/Makassar | 13 | 'Asia/Jakarta': 28, 'Asia/Makassar': 1 | Text / String |
| membership_expired_date | DATE | 10 | Yes | 0 | 100.00% | 9 | 2024-03-31 | 2026-03-04 | 10 | '2026-03-04': 13, '2025-05-12': 7, '2025-08-20': 2 | YYYY-MM-DD Date |
| is_deleted | BOOLEAN | 1 | No | 0 | 100.00% | 2 | False | True | Not a string | 'False': 28, 'True': 1 | Boolean Flag |

## 2. Table: `user_referral_statuses`

| Column Name | Data Type | Defined Length | Nulls Allowed | Null Count | % Populated | Distinct Value Count | Minimum Value | Maximum Value | Max Actual Length | Top Frequencies | Detected Pattern |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| id | INTEGER | 10 | No | 0 | 100.00% | 3 | 1 | 3 | Not a string | '1': 1, '3': 1, '2': 1 | Numeric Integer |
| description | VARCHAR | 50 | No | 0 | 100.00% | 3 | Berhasil | Tidak Berhasil | 14 | 'Menunggu': 1, 'Tidak Berhasil': 1, 'Berhasil': 1 | Text / String |
| created_at | TIMESTAMP | 24 | No | 0 | 100.00% | 2 | 2024-03-08T08:49:37Z | 2024-03-08T10:07:10Z | 20 | '2024-03-08T10:07:10Z': 2, '2024-03-08T08:49:37Z': 1 | ISO8601 Timestamp |

## 2. Table: `referral_rewards`

| Column Name | Data Type | Defined Length | Nulls Allowed | Null Count | % Populated | Distinct Value Count | Minimum Value | Maximum Value | Max Actual Length | Top Frequencies | Detected Pattern |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| id | INTEGER | 10 | No | 0 | 100.00% | 3 | 1 | 3 | Not a string | '1': 1, '3': 1, '2': 1 | Numeric Integer |
| reward_value | VARCHAR | 20 | No | 0 | 100.00% | 3 | 10 days | 20 days | 7 | '10 days': 1, '15 days': 1, '20 days': 1 | Text / String |
| created_at | TIMESTAMP | 24 | No | 0 | 100.00% | 3 | 2024-03-13T02:44:32Z | 2024-03-13T02:45:15Z | 20 | '2024-03-13T02:44:32Z': 1, '2024-03-13T02:45:15Z': 1, '2024-03-13T02:45:11Z': 1 | ISO8601 Timestamp |
| reward_type | INTEGER | 5 | No | 0 | 100.00% | 1 | 1 | 1 | Not a string | '1': 3 | Numeric Integer |

## 2. Table: `paid_transactions`

| Column Name | Data Type | Defined Length | Nulls Allowed | Null Count | % Populated | Distinct Value Count | Minimum Value | Maximum Value | Max Actual Length | Top Frequencies | Detected Pattern |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| transaction_id | VARCHAR | 32 | No | 0 | 100.00% | 14 | 07f21743663aacb7d212c286d47a14de | f192fca27d438c053db425fade152d66 | 32 | '1d1eb8a9e864a1cccb2d850398461807': 1, '8623f36f36e709fbefe43defcac59583': 1, '93d48d85048e102d32d02df43138d283': 1 | Hex32 (MD5/UUID Hash) |
| transaction_status | VARCHAR | 20 | No | 0 | 100.00% | 1 | PAID | PAID | 4 | 'PAID': 14 | Text / String |
| transaction_at | TIMESTAMP | 24 | No | 0 | 100.00% | 14 | 2024-05-01T05:07:30.374Z | 2024-05-21T09:47:11.535Z | 24 | '2024-05-02T04:49:01.497Z': 1, '2024-05-02T07:53:43.179Z': 1, '2024-05-20T04:23:09.444Z': 1 | ISO8601 Timestamp |
| transaction_location | VARCHAR | 50 | Yes | 0 | 100.00% | 6 | ADITYAWARMAN | SUNSET ROAD | 19 | 'ADITYAWARMAN': 4, 'ARTERI PONDOK INDAH': 3, 'GREENVILLE': 3 | Text / String |
| timezone_transaction | VARCHAR | 30 | Yes | 0 | 100.00% | 2 | Asia/Jakarta | Asia/Makassar | 13 | 'Asia/Jakarta': 13, 'Asia/Makassar': 1 | Text / String |
| transaction_type | VARCHAR | 20 | No | 0 | 100.00% | 2 | NEW | REJOIN | 6 | 'NEW': 13, 'REJOIN': 1 | Text / String |

## 2. Table: `lead_log`

| Column Name | Data Type | Defined Length | Nulls Allowed | Null Count | % Populated | Distinct Value Count | Minimum Value | Maximum Value | Max Actual Length | Top Frequencies | Detected Pattern |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| id | INTEGER | 10 | No | 0 | 100.00% | 8 | 1 | 8 | Not a string | '1': 1, '2': 1, '3': 1 | Numeric Integer |
| lead_id | VARCHAR | 32 | No | 0 | 100.00% | 5 | 08b8ab0371b6a0cb79319628505c446c | c50f607bbae83f7c53551476e11997eb | 32 | '08b8ab0371b6a0cb79319628505c446c': 4, '774656feb3119be1d8d6d893429c7cc0': 1, 'bbd3c7b2448041dc5339b23878cacd79': 1 | Hex32 (MD5/UUID Hash) |
| source_category | VARCHAR | 30 | Yes | 0 | 100.00% | 2 | Offline | Online | 7 | 'Online': 7, 'Offline': 1 | Text / String |
| created_at | TIMESTAMP | 24 | No | 0 | 100.00% | 5 | 2024-01-31T08:53:22.403Z | 2024-05-13T06:38:58.322Z | 24 | '2024-05-01T02:54:03.482Z': 4, '2024-05-13T06:38:58.322Z': 1, '2024-05-10T04:16:27.919Z': 1 | ISO8601 Timestamp |
| preferred_location | VARCHAR | 50 | Yes | 0 | 100.00% | 3 | ADITYAWARMAN | GAJAH MADA | 12 | 'BENHIL': 6, 'GAJAH MADA': 1, 'ADITYAWARMAN': 1 | Text / String |
| timezone_location | VARCHAR | 30 | Yes | 0 | 100.00% | 1 | Asia/Jakarta | Asia/Jakarta | 12 | 'Asia/Jakarta': 8 | Text / String |
| current_status | VARCHAR | 30 | Yes | 0 | 100.00% | 5 | Appointment | Warm | 11 | 'Fresh': 3, 'Deal': 2, 'Warm': 1 | Text / String |

