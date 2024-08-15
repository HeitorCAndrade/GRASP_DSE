#ifndef LPC_H
#define LPC_H
#include "private.h"

void
Autocorrelation (word * s /* [0..159]     IN/OUT  */ ,
		 longword * L_ACF /* [0..8]       OUT     */ );

void
Reflection_coefficients (longword * L_ACF /* 0...8        IN      */ ,
			 register word * r /* 0...7        OUT     */ );


void
Transformation_to_Log_Area_Ratios (register word * r /* 0..7    IN/OUT */ );

void
Quantization_and_coding (register word * LAR /* [0..7]       IN/OUT  */ );

void
Gsm_LPC_Analysis ();




#endif