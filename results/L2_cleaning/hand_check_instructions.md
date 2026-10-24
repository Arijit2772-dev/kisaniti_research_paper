# Hand check of 56 rows against the AGMARKNET website

For each line of `hand_check_sheet.csv`: open the AGMARKNET report *Date Wise Prices for Specified Commodity* for Paddy(Basmati), Punjab, `month_to_select`, find `market_to_find`, and fill the `web_*` columns with what the page shows for that variety and date.

**The key question for blank-date rows (`date_inferred = 1`):** on the website, is the variety's row shown under the date of the row above it (one date cell spanning two rows)? Answer in `web_row_shows_under_previous_date_merged_cell_yes_no`. If yes for all of them, the blank-date rule is confirmed. If the page shows a different date, or no such row, write that in `notes`.

Set `agrees_yes_no` to yes only when date, arrivals and all three prices match the file. Write your name in `checked_by` and the date in `checked_on`.

Rows per stratum: A_problem_flag 8, B_blank_own_arrivals 3, B_blank_shared_arrivals 17, C_extreme_high 3, C_extreme_low 3, D_ordinary 16, E_modal_equals_msp_value 4, F_largest_arrivals 2.

Strata C are described only by how far the price is from its season median; they are NOT an outlier rule. Prices of exactly the same value in min, max and modal are normal for many small mandis.
