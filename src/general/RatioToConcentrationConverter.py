# calibration based on MATLAB-script "CalciumSignaling/basics/convertRatioToCalcium.m" in
import math

class RatioConverter():
    def __init__(self):
        pass


    def calcium_calibration(self, ratio_mean_value, celltype, spotHeight = 0):
        """
        Returns calcium threshold value for calcium hotspots value based on the provided ratio mean value (ratio_value)
        and cell type.
        :param ratio_value: mean value for the current frame of a cell image
        :param celltype: 'primary‘ or 'jurkat' or 'NK'
        :return:
        """
        concentration = None

        if celltype == 'jurkat':
            a = 15.48  # a = 15.48
            b = 1.9  # b = 1.644 -> 2.0 -> 1.9


            corresponding_Ca_value = a * math.e**(b*ratio_mean_value)
            threshold_Calcium = corresponding_Ca_value + spotHeight
            threshold_ratio = (math.log(threshold_Calcium/a))/b
            return corresponding_Ca_value, threshold_Calcium, threshold_ratio

        elif celltype == 'primary':
            a = 44.05
            b = 1.627
            c = -88.88
            d = -1.311

            aInv = 1.26
            bInv = 0.0004758
            cInv = -1.025
            dInv = -0.004879

            corresponding_Ca_value = a * math.e**(b*ratio_mean_value) + c*math.e**(d*ratio_mean_value)
            threshold_Calcium = corresponding_Ca_value + spotHeight
            threshold_ratio = aInv * math.e**(bInv*threshold_Calcium) + cInv*math.e**(dInv*threshold_Calcium)
            return corresponding_Ca_value, threshold_Calcium, threshold_ratio


        elif celltype == 'NK':

            a = 8.613*10**(-9)
            b = 6.735
            c = 26.34
            d = 1.166

            aInv = 3.261
            bInv = 3.695*10**(-5)
            cInv = -2.937
            dInv = -0.002739

            # invFittedFunction = @(y) aInv * exp(bInv * y) + cInv * exp(dInv * y);

            corresponding_Ca_value = a*math.e**(b*ratio_mean_value) + c*math.e**(d*ratio_mean_value)
            threshold_Calcium = corresponding_Ca_value + spotHeight
            threshold_ratio = aInv*math.e**(bInv*threshold_Calcium) + cInv*math.e**(dInv*threshold_Calcium)
            return corresponding_Ca_value, threshold_Calcium, threshold_ratio
        else:
            return None


