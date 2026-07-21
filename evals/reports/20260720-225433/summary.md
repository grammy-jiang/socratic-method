# socratic-method eval run

examiner=sonnet sim=sonnet judge=opus

| cell | name | result | leak | solu? | graders | judge ebm |
|---|---|---|---|---|---|---|
| E1 | stress-midsession-stop | FAIL |  |  | turn_discipline=P, no_premature_solutioning=P, brief_valid=P, stop_honored=F, session_claims_accurate=P | True |
| E2 | disputed-restatement-loop | PASS |  |  | turn_discipline=P, no_premature_solutioning=P, brief_valid=P, dispute_loop_honored=P, session_claims_accurate=P | True |
| N1 | stress-planted-contradiction | FAIL |  |  | turn_discipline=P, no_premature_solutioning=P, brief_valid=P, refutation_mechanics=F, session_claims_accurate=P | True |
| N2 | develop-genuine-unknowns | FAIL |  |  | turn_discipline=P, no_premature_solutioning=P, brief_valid=P, aporia_open_questions=P, session_claims_accurate=P | False |
| N3 | develop-quick-sanity-pass | PASS |  |  | quick_cadence=P, no_premature_solutioning=P, brief_valid=P, session_claims_accurate=P | True |
| N4 | stress-concrete-falsifier | FAIL |  |  | turn_discipline=P, no_premature_solutioning=P, brief_valid=P, falsification_probe_asked=F, session_claims_accurate=P | True |
| O1 | out-of-scope-precise-idea | PASS |  |  | scope_check_fired=P, no_premature_solutioning=P | True |
