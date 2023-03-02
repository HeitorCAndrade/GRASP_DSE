set_directive_dependence -type inter -dependent true "update_knn/FIND_MAX_DIST"
set_directive_pipeline "knn_vote/knn_vote_label1"
set_directive_unroll -factor 20 "DigitRec_sw/TEST_LOOP"
set_directive_unroll -factor 2 "DigitRec_sw/SET_KNN_SET"
set_directive_unroll -factor 500 "DigitRec_sw/TRAINING_LOOP"
