# Multiple Loop Directive HLS Dataset

This is the source code used for the generation of the MLDHLS dataset, which can be accessed here: http://www.inf.ufrgs.br/~glnazar/MLDHLS.tar.gz

The dataset currently contains 10 benchmarks: SHA, GSM, AES, ADPCM, TRANS_FFT, GEMM, KNN , STENCIL3D, GRAMSCHMIDT, BACKPROP.

Each benchmark contains several different design points based on the directives applied. For each design point you will find:

	- Source C code.

	- LLVM Intermediate Representation (IR).

	- ADB files.

	- Generated RTL files (Verilog).

	- Post HLS and post implementation reports for timming, resource usage, power and number of clock cycles.

# Usage

```
python main.py -b <benchmark name> -i <number of instances> -t <max run time for each instance in seconds>
```
`benchmark name`: current benchmarks already included: SHA, GSM, AES, SPAM, DIGIT, OPTICAL, ADPCM, MOTION, TRANS_FFT, GEMM, KNN, VITERBI, STENCIL3D, GRAMSCHMIDT, BACKPROP - benchmark codes retrieved from CHStone, Machsuite, Polybench and Rosetta bechmarks.

some other useful parameters include:

`-bi`: Generates base instances first (counting towards the specified number of instances specified by `-i`).

`-r`: Resumes run if a `stored_permutations.json` file is found (created automatically).

`-v`: Verify which runs are valid for use, i.e. runs with successful implementation process.

## Modifying benchmark for usage
In order to add a new benchmark, update the `benchmarks.json` file by adding the following:

```
"<benchmark_name>": {"cFiles":["path/to/file1", "path/to/file2", ... , "path/to/fileN"], "dFile":"<directive json file path>", "prjFile":"<top function name>"}
```

To apply directives to a C/C++ program we need to know where to apply these directives. That is what labels serves for. Here is an example:
```
sha_transform ()
{
  int i;
  INT32 temp, A, B, C, D, E, W[80];

  sha_transform_label1:for (i = 0; i < 16; ++i)
    {
      W[i] = sha_info_data[i];
    }
  sha_transform_label2:for (i = 16; i < 80; ++i)
    {
      W[i] = W[i - 3] ^ W[i - 8] ^ W[i - 14] ^ W[i - 16];
    }
    ....
```
The piece of code above has two labels: `sha_transform_label1` and `sha_transform_label2`. They are needed for directives that are applied to these loops, like `pipeline`and `unroll`. However, not all directives need an additional label for them to work, some directives are applied to a function or a variable, in these case their own names will be the 'label'. An example of this would be a `loop_merge` on the `sha_transform`function above. 
For demonstration, if we had applied `pipeline`in the two loops above and a `loop_merge` on the function, the `directives.tcl`file generated would be like this: 
```
set_directive_loop_merge "sha_transform"
set_directive_pipeline "sha_transform/sha_transform_label1"
set_directive_pipeline "sha_transform/sha_transform_label2"
```

### Directives Json File

The directive Json file should contain the target directives as well as its setting variations

This file has the following format:
```
{

"directives":
	{
	
	"<directive_type> <label>": {
		"possible_directives":["",
		<directive1>,<directive2>],
		"function": <function in which directive is located>,
		"label": <label in which directive is applied>,
		"directive_type":<directive_type>
	},
	...

},
"nested_loops":
	[
	
		{
		    "function":<function where loop is located>,
		    "label":<loop label>,
		    "nest": {
		        "function":<function where loop is located>,
		        "label":<loop label>,
		        "nest": {
				        ...
		        }
		    }
		},
		...	
	]
}
```
Each dictionary inside `"directives"`is what I call a 'directive group', in other words, using the example above, this would be the directive group:
```
"<directive_type> <label>": {
		"possible_directives":["",
		<directive1>,<directive2>],
		"function": <function in which directive is located>,
		"label": <label in which directive is applied>,
		"directive_type":<directive_type>
	},
```
In each directive group, the primary information is the `"possible_directives"`, it lists all the directives in the directive group, including the empty directive `""`.

 In a concrete example: 
 ```
"pipeline flow_calc_label23": {
	   "possible_directives":["","set_directive_pipeline \"flow_calc/flow_calc_label23\""],
	   "function":"flow_calc",
	   "label": "flow_calc_label23",
	   "directive_type":"pipeline"
},
 ```

