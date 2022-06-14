set_directive_pipeline "main/main_label0"
set_directive_pipeline "local_memcpy/local_memcpy_label3"
set_directive_loop_merge "sha_transform"
set_directive_pipeline "sha_update/sha_update_label4"
set_directive_unroll -factor 8 "sha_update/sha_update_label4"
set_directive_pipeline "sha_transform_label1"
set_directive_unroll "sha_transform_label1"
set_directive_pipeline "sha_transform_label2"
set_directive_unroll "sha_transform_label2"
set_directive_pipeline "sha_transform_label3"
set_directive_unroll "sha_transform_label3"
set_directive_pipeline sha_transform_label4
set_directive_unroll "sha_transform_label4"
set_directive_pipeline sha_transform_label5
set_directive_unroll "sha_transform_label5"
set_directive_pipeline sha_transform_label6
set_directive_unroll "sha_transform_label6"
set_directive_array_partition -type block -factor 32 -dim 1 "sha_transform" W
set_directive_inline -region "sha_stream"
