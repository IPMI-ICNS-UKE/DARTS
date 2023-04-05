
class CellImage:
    def __init__(self, roi1, roi2):
        self.channel1 = roi1
        self.channel2 = roi2
        self.steps_executed = []
        self.ratio = None


    def channel_registration(self):
        # TODO: implement channel registration
        print("Here comes the channel registration")
        # registration of channel 1 and 2
        pass

    #def execute_processing_step(self, step, parameters):
    #    if (isinstance(step, MembraneSegmentation)):
    #        segmentedMembraneMask = step.execute(self.channel1, self.channel2, parameters) # not very handsome code
    #        self.channel1 = step.applyMembraneMask(self.channel1, segmentedMembraneMask)
    #        self.channel2 = step.applyMembraneMask(self.channel2, segmentedMembraneMask)
    #    elif (isinstance(step, RatioCalculation)):
    #        self.channel1 = step.execute(self.channel1, self.channel2, parameters)
    #        self.channel2 = step.execute(self.channel1, self.channel2, parameters)
    #    else:
    #        self.channel1 = step.execute(self.channel1, parameters)
    #        self.channel2 = step.execute(self.channel2, parameters)

    #    self.steps_executed.append(step.give_name())

    def calculate_ratio(self):
        ratio = self.channel1.return_image()/self.channel2.return_image()
        return ratio



class ChannelImage:
    def __init__(self, roi, wl):

        # ((y1, y2), (x1, x2)) = roi_coord
        # self.image = image[:, y1:y2, x1:x2]
        self.image = roi
        self.wavelength = wl

    def return_image(self):
        return self.image

    def return_membrane (self):
        return self.membrane

    def getWavelength (self):
        return self.wavelength

