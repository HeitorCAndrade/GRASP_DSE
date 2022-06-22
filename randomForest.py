from sklearn import ensemble
from sklearn.preprocessing import Normalizer
from estimator import Estimator
import re
from preProcessor import PreProcessor
from solution import Solution

class RandomForestEstimator(Estimator):
    processor = PreProcessor()
    def __init__(self):
        self.rfRegressor=ensemble.RandomForestRegressor(n_estimators=100)
        self.features = None
        self.results = None

    def trainModel(self,dataset):
        """
        Build a forest of trees from the dataset.

        Parameters
        ----------
        dataset: List of Solution objects
        """
        self.features, self.results = self.processor.process(dataset)
        self.rfRegressor.fit(self.features,self.results) #train
        
    def trainModelPerMetric(self,metric):
        #TODO
        self.rfRegressor.fit(self.features,self.results) #train

    def estimateSynthesis(self, processedFeatures):
        """
        Estimate the output of synthesis from the dataset.

        Parameters
        ----------
        dataset: List of Solution objects

        Returns
        -------
        List : List of the output([FF,DSP,LUT,BRAM,resources,latency],[...],...)
                estimated for these features
        """
        #processedFeatures =  self.processor.process(X)
        return self.rfRegressor.predict(processedFeatures)
    
    def score(self,dataset):
        return self.rfRegressor.score(xTeste,yTeste)



#usar scikit learn pra decisions tree
#testar treino com multi-outputs (prever todas metricas) e testar com varios modelos (um pra cada metrica)
#USAR 80% para treino e 20% para teste
#Titulos dos features de cada coluna vao ser sobre o label e o tipo de diretiva. Ex: 
#             unroll sha_update_label4                         |               pipeline sha_update_label4             |                   array_partition main                                   | Saída(em LUTS por exemplo)
# set_directive_unroll -factor 8 "sha_update/sha_update_label4"| set_directive_pipeline "sha_update/sha_update_label4"|set_directive_array_partition -type block -factor 100 -dim 0 "main" indata|         45

#Posso trocar esses nomes por numeros, de acordo com o dicionario de diretivas feitos passando as diretivas para fileParser() (ou parsedTxt())
# o dicionário será tipo: dicionario[pipeline] = ['',pipe 1, pipe2], então posso ao invés de colocar '' ou pipe1 ou pipe2 na tabela, posso colocar 0,1,2. EX:

# unroll sha_update_label4 | pipeline sha_update_label4 | array_partition main  | Saída(em LUTS por exemplo)
#          1               |            1               |          2            |            45

#O problema disso é que são categorical variables, portanto devo ajeitar isso com one hot encoding

