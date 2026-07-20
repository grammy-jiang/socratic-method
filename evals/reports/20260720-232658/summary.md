# socratic-method eval run

examiner=sonnet sim=sonnet judge=opus

| cell | name | result | leak | solu? | graders | judge ebm |
|---|---|---|---|---|---|---|
| E1 | stress-midsession-stop | PASS |  |  | turn_discipline=P, no_premature_solutioning=P, brief_valid=P, stop_honored=P, session_claims_accurate=P | True |
| N1 | stress-planted-contradiction | FAIL |  |  | turn_discipline=P, no_premature_solutioning=P, brief_valid=P, refutation_mechanics=F, session_claims_accurate=P | None |
| N2 | develop-genuine-unknowns | PASS |  |  | turn_discipline=P, no_premature_solutioning=P, brief_valid=P, aporia_open_questions=P, session_claims_accurate=P | True |
| N4 | stress-concrete-falsifier | FAIL |  |  | turn_discipline=P, no_premature_solutioning=P, brief_valid=P, falsification_probe_asked=F, session_claims_accurate=P | False |
