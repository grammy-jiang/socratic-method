# socratic-method eval run

examiner=sonnet sim=sonnet judge=opus

| cell | name | result | leak | solu? | graders | judge ebm |
|---|---|---|---|---|---|---|
| N3 | develop-quick-sanity-pass | FAIL |  |  | quick_cadence=F, no_premature_solutioning=P, brief_valid=P, session_claims_accurate=P | True |
| O1 | out-of-scope-precise-idea | FAIL |  |  | scope_check_fired=F, no_premature_solutioning=P | False |
