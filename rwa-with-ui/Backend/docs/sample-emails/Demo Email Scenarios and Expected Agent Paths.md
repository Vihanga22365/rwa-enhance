# Demo Email Scenarios for RWA / Collateral Investigation Agent

These four synthetic cases use only the two demo GFC IDs:

- `1123456918`
- `1123456567`

They are designed against the companion workbooks:

- `Main Data - Email Scenario Demo.xlsx`
- `Issue Types and Steps - Email Scenario Demo.xlsx`

The intent is to demonstrate:
1. A standard decision-tree case that resolves automatically.
2. An inconclusive case that requires a human-directed one-off check.
3. A second standard decision-tree case that resolves automatically.
4. A second inconclusive case, followed by a human-directed check and then a case-scoped what-if simulation.

---

## Case 1 — Collateral drop resolved by SWWR

### Front-desk email

**Subject:** RE: GFCID '1123456918' — security '4917989V8' dropped collateral

Hi team,

Can you please check why security `4917989V8` under GFCID `1123456918` is getting materially reduced collateral value? I would expect this to be impacting PSE / RWA as well.

Thanks.

### Expected issue classification

`Collateral Market Value drop observed for Inbound trades`

### Expected standard-tree traversal

1. GFC exists in `om_cdm_rwa_mtrc`.
2. Security `4917989V8` is found.
3. Recognized inbound balance type `15` exists.
4. `FDL_FX_AMT = 1,296,833.3333`.
5. `BUY_SELL_IND = B`.
6. `NETG_AGR_ID = 2123783`.
7. `src_txn_id = 202505198123456SN5`.
8. `LGL_CERTAINTY_FLG = Y`, so legal-remediation checks are skipped.
9. `lrm_flg = Y`.
10. `IS_DAILY_MARGN = Y`.
11. `stale_prc_flg_2days = N`.
12. `stale_prc_flg_6mths = N`.
13. `haircut_eligible_status = Eligible`.
14. `swwr_flag = Y`.
15. `swwr_recovery_rate = 0.65`.

### Expected stopping criterion

Stop on the SWWR check.

**Expected agent conclusion:** the current data supports a collateral-recognition reduction associated with **Specific Wrong-Way Risk (SWWR)** treatment. The affected Mart collateral amount is approximately `1.297m`, and the configured SWWR recovery rate is `65%`.

---

## Case 2 — Collateral drop initially inconclusive, then resolved by a human-directed check

### Front-desk email

**Subject:** RE: GFCID '1123456918' — security '78462A1K3' collateral benefit looks low

Hi team,

Can you check why security `78462A1K3` under GFCID `1123456918` is showing lower collateral benefit? I do not see an obvious legal-certainty or eligibility issue.

Thanks.

### Expected issue classification

`Collateral Market Value drop observed for Inbound trades`

### Expected standard-tree traversal

The agent finds:

- `SCR_ID = 78462A1K3`
- `BAL_TYP_CD = 16`
- `FDL_FX_AMT = 810,000`
- `BUY_SELL_IND = B`
- `NETG_AGR_ID = 2123783`
- `LGL_CERTAINTY_FLG = Y`
- `lrm_flg = Y`
- `IS_DAILY_MARGN = Y`
- stale-price flags are both `N`
- haircut status is `Eligible`
- `swwr_flag = N`
- Mart / Mart Extn reconciliation passes for balance type `16`

No standard-tree stopping criterion explains a historical collateral drop.

### Expected initial agent conclusion

**INCONCLUSIVE / HUMAN REVIEW REQUIRED**

The current-state Mart and Mart Extn data do not identify a cause. The standard tree should explicitly say that it cannot prove why the value *dropped over time* because no prior-period snapshot is available.

### Human follow-up — one-off check

> For this case only, please run one additional check outside the standard decision tree.  
> For `src_txn_id = 202505208123456SN6`, confirm whether both inbound balance types `15` and `16` are present in `om_cdm_rwa_mtrc`. We expect both. If one is missing, flag that as a possible upstream balance-population break.

### Expected follow-up result

The agent finds:

- BAL_TYP_CD `16` exists.
- BAL_TYP_CD `15` does **not** exist for `src_txn_id = 202505208123456SN6`.

**Expected human-directed conclusion:** the one-off check identifies a missing expected balance-type-15 record. The agent should label this as an **AD HOC FOLLOW-UP finding**, not as a conclusion produced by the standard decision tree.

---

## Case 3 — RWA increase resolved through legal-certainty remediation / country assessment

### Front-desk email

**Subject:** RE: GFCID '1123456567' — high RWA / LC N on security '6G061567B'

Hi team,

We are seeing high RWA for GFCID `1123456567` on security `6G061567B` / source transaction `202501978123456SN5`.

Can you confirm whether this is being driven by the LC=N treatment, or whether the agreement should still qualify for remediation / netting benefit?

Thanks.

### Expected issue classification

`RWA change observed for a counterparty or transaction`

### Expected standard-tree traversal

1. GFC and source transaction are found.
2. Recognized balance type `15` exists.
3. `FDL_FX_AMT = 8,830,003.084`.
4. Netting agreement exists.
5. `LGL_CERTAINTY_FLG = N`.
6. Mart Extn `original_lgl_certainty_flg = N`.
7. `ovr_imm_cancellable = LIMITED`, so the demo remediation route remains possible.
8. `incorp_cntry_assessment = FAIL`.

### Expected stopping criterion

Stop at the incorporated-country assessment.

**Expected agent conclusion:** the available evidence supports an **exposure-side RWA driver**: legal certainty is not available, and the bank-specific country assessment blocks the remediation route, so normal netting/collateral benefit is not available for this balance.

---

## Case 4 — RWA initially inconclusive, human-directed mapping check, then simulation

### Front-desk email

**Subject:** RE: GFCID '1123456567' — RWA looks high for security '9N2026PZ4'

Hi team,

Can you check why RWA looks high for security `9N2026PZ4`, source transaction `202502018123456SN6`, under GFCID `1123456567`?

Legal certainty appears to be fine, so I expected collateral recognition to be available.

Thanks.

### Expected issue classification

`RWA change observed for a counterparty or transaction`

### Expected standard-tree traversal

The scoped Mart row contains:

- `SCR_ID = 9N2026PZ4`
- `src_txn_id = 202502018123456SN6`
- `BAL_TYP_CD = 17`
- `FDL_FX_AMT = 2,210,000`
- `NETG_AGR_ID = 2253783`
- `LGL_CERTAINTY_FLG = Y`

The standard RWA tree only treats balance types `15` and `16` as recognized inbound-collateral rows for this demo. Therefore:

1. The transaction is found.
2. No recognized `15/16` collateral row is retained for this transaction.
3. The standard 15/16 collateral-eligibility checks are marked not applicable.
4. No exposure-side root cause is proven.
5. The two sheets do not contain PD, LGD, maturity, internal rating, effective risk weight, or model-version data.

### Expected initial agent conclusion

**INCONCLUSIVE / HUMAN REVIEW REQUIRED**

The current standard decision tree cannot determine whether the RWA movement is exposure-side or risk-weight-side for this transaction.

### Human follow-up — one-off expected-mapping check

> For this case only, upstream says this transaction should have been treated as inbound balance type `16`, not `17`.  
> Please inspect the Mart Extn record for GFCID `1123456567`, balance type `16`, and tell me the first eligibility check that would fail if that expected mapping were used.

### Expected follow-up result

For GFCID `1123456567`, BAL_TYP_CD `16`:

- `original_lgl_certainty_flg = Y`
- `lrm_flg = N`
- `IS_DAILY_MARGN = Y`
- `stale_prc_flg_2days = Y`
- `stale_prc_flg_6mths = N`
- `haircut_eligible_status = Eligible`
- `swwr_flag = N`

The first failure in the normal sequence is:

**`lrm_flg = N`**

The agent should label this result **HUMAN-DIRECTED**, because the standard tree did not infer that balance type `17` should be remapped to `16`.

### Operations-user simulation follow-up

> Please run a what-if simulation for this case only.  
> Assume the transaction is mapped to BAL_TYP_CD `16` and assume `lrm_flg = Y`. Do not change the source data. Continue the standard RWA decision tree from the next check and tell me where it stops.

### Expected simulation result

Under the hypothetical override:

1. `lrm_flg` is treated as `Y` for the simulation.
2. `IS_DAILY_MARGN = Y` passes.
3. `stale_prc_flg_2days = Y` fails.

**Expected simulated conclusion:** even if the LRM condition were forced to pass, the collateral would next fail the short-term stale-price check. The agent should clearly label this result **HYPOTHETICAL** and leave the underlying workbook unchanged.

---

# Demo coverage summary

| Case | Issue Type | GFC ID | Initial Result | Follow-up |
|---|---|---:|---|---|
| 1 | Collateral MV drop | 1123456918 | Resolved — SWWR | None |
| 2 | Collateral MV drop | 1123456918 | Inconclusive | Human-directed missing balance-type check |
| 3 | RWA change | 1123456567 | Resolved — country assessment blocks remediation | None |
| 4 | RWA change | 1123456567 | Inconclusive | Human-directed mapping check + LRM what-if simulation |

