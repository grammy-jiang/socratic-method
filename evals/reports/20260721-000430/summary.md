# socratic-method eval run

examiner=sonnet sim=sonnet judge=opus

| cell | name | result | leak | solu? | graders | judge ebm |
|---|---|---|---|---|---|---|
| E1 | stress-midsession-stop | FAIL |  |  | turn_discipline=P, no_premature_solutioning=P, brief_valid=P, stop_honored=F, session_claims_accurate=P | True |
| E2 | disputed-restatement-loop | FAIL |  |  | turn_discipline=P, no_premature_solutioning=P, brief_valid=F, dispute_loop_honored=P, session_claims_accurate=F | True |
| N1 | stress-planted-contradiction | FAIL |  |  | turn_discipline=P, no_premature_solutioning=P, brief_valid=P, refutation_mechanics=F, session_claims_accurate=P | True |
| N2 | develop-genuine-unknowns | PASS |  |  | turn_discipline=P, no_premature_solutioning=P, brief_valid=P, aporia_open_questions=P, session_claims_accurate=P | True |
| N3 | develop-quick-sanity-pass | PASS |  |  | quick_cadence=P, no_premature_solutioning=P, brief_valid=P, session_claims_accurate=P | True |
| N4 | stress-concrete-falsifier | PASS |  |  | turn_discipline=P, no_premature_solutioning=P, brief_valid=P, falsification_probe_asked=P, session_claims_accurate=P | True |
| O1 | out-of-scope-precise-idea | FAIL |  |  | scope_check_fired=P, no_premature_solutioning=P | None |
