# calibration based on MATLAB-script "CalciumSignaling/basics/convertRatioToCalcium.m" in
import math
import numpy as np

class RatioConverter():
    def __init__(self):
        pass

    def convert_ratio_to_concentration(self, celltype, ratio):
        if celltype == 'jurkat':
            a = 15.48
            b = 1.644
            concentration = a * math.e**(b*ratio)
            return concentration

        elif celltype == 'primary':
            a = 44.05
            b = 1.627
            c = -88.88
            d = -1.311
            concentration = a * math.e**(b*ratio) + c*math.e**(d*ratio)
            return concentration

        elif celltype == 'NK 2023':
            a = 8.613*10**(-9)
            b = 6.735
            c = 26.34
            d = 1.166

            # aInv = 3.261
            # bInv = 3.695*10**(-5)
            # cInv = -2.937
            # dInv = -0.002739

            # invFittedFunction = @(y) aInv * exp(bInv * y) + cInv * exp(dInv * y);

            concentration = a*math.e**(b*ratio) + c*math.e**(d*ratio)
            return concentration
        else:
            return None

    def give_signal_threshold_in_nM(self, cell_type):
        """
        Returns the signal threshold in nM for a specific cell type.
        :param cell_type:
        :return:
        """
        if cell_type == 'jurkat':
            return 72.0
        elif cell_type == 'primary':
            return 112.5
        else:
            return None

    def give_signal_threshold_as_ratio(self, cell_type):
        if cell_type == 'jurkat':
            signal_threshold_in_nM = self.give_signal_threshold_in_nM(cell_type)  # 72nM = 15,48 * e**(1,644*ratio)
            threshold_ratio = (np.log(signal_threshold_in_nM/15.48))/1.644
            return threshold_ratio
        elif cell_type == 'primary':
            # 112.5 = 44.05*e**(1.627*ratio) - 88.88*e**(-1.311*ratio)
            ratio = 0.7377140602
            return ratio
        else:
            return None

