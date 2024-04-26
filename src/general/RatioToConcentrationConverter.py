# calibration based on MATLAB-script "CalciumSignaling/basics/convertRatioToCalcium.m" in
import math

class RatioConverter():
    def __init__(self, parameter_dict):
        self.parameter_dict = parameter_dict


    def calcium_calibration(self, ratio_value, celltype, spotHeight = 0):
        """
        Returns calcium threshold value for calcium hotspots value based on the provided ratio mean value (ratio_value)
        and cell type.
        :param ratio_value: mean value for the current frame of a cell image
        :param celltype: 'primary‘ or 'jurkat' or 'NK'
        :return:
        """

        if celltype == 'jurkat':
            a = 15.48  # a = 15.48
            b = 1.9  # b = 1.644 -> 2.0 -> 1.9


            corresponding_Ca_value = a * math.e**(b*ratio_value)
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

            corresponding_Ca_value = a * math.e**(b*ratio_value) + c*math.e**(d*ratio_value)
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

            corresponding_Ca_value = a*math.e**(b*ratio_value) + c*math.e**(d*ratio_value)
            threshold_Calcium = corresponding_Ca_value + spotHeight
            threshold_ratio = aInv*math.e**(bInv*threshold_Calcium) + cInv*math.e**(dInv*threshold_Calcium)
            return corresponding_Ca_value, threshold_Calcium, threshold_ratio

        else:

            kd_value = self.parameter_dict['KD value (of Ca2+ dye) [nM]']
            min_ratio = self.parameter_dict['minimum ratio']
            max_ratio = self.parameter_dict['maximum ratio']
            min_intensity = self.parameter_dict['minimum fluorescence intensity']
            max_intensity = self.parameter_dict['maximum fluorescence intensity']
            spotHeight = self.parameter_dict['spot Height Ca2+ microdomains']

            corresponding_Ca_value = kd_value*((ratio_value-min_ratio)/(max_ratio-ratio_value))*(min_intensity/max_intensity)
            threshold_Calcium = corresponding_Ca_value + spotHeight
            threshold_ratio = (threshold_Calcium * (max_ratio - min_ratio) * max_intensity) / (kd_value * min_intensity + threshold_Calcium * max_intensity) + min_ratio

            return corresponding_Ca_value, threshold_Calcium, threshold_ratio


