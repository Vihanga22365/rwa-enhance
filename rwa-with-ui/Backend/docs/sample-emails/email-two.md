RE: GFCID '1123456918' dropped collateral

Can you please check why highlighted security '4917989V8' is getting no collateral value? I would imagine that this is impacting PSE as well.

---

RE: GFCID '1123456567' LC N RWA question

Hi team,

Seeing high RWA with GFCID '1123456567' on 6/16 due to LC N issue but can you please confirm that this is driven by "Forward Settling Indicator" being "Y"?
And if that is the case, there are all going to be <1Y trades so shouldn't these get 20% factor applied?

follow :
Check if either of stale_prc_flg_2days OR stale_prc_flg_6mths is N in Mart Extn table. If condition is false, collateral cannot be used as the Price is Stale.

---

RE: PSE SFT - GFCID '1123456039' - REPO trading netting ineligible (mc03016) INC0139083360

Hi Optima, Gareth,

Would you be able to advise about the below exposure? It is coming from illiquid MV due to DSFT Base Level concentration value reported as of September 11th. Is this expected?
