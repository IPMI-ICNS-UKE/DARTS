from pathlib import Path
import tomli
from postprocessing.processing import ImageProcessor
from postprocessing.registration import Registration_SITK, Registration_SR
import matplotlib.pyplot as plt

parameters = tomli.loads(Path("config.toml").read_text(encoding="utf-8"))

Processor = ImageProcessor(parameters)

channel1 = Processor.channel1
channel2 = Processor.channel2


Reg_SITK = Registration_SITK()
Reg_SR = Registration_SR()

channel2_registered_SR = Reg_SR.channel_registration(channel1, channel2)

channel2_registered_SITK_framebyframe = Reg_SITK.channel_registration(channel1, channel2, framebyframe=True)
channel2_registered_SITK = Reg_SITK.channel_registration(channel1, channel2, framebyframe=False)

#%%


f1 = 0
f2 = 5
f3 = 9

fig, ax = plt.subplots(ncols=4, nrows=3, figsize = [10,10])
ax[0, 0].imshow(channel1[f1]/channel2[f1])
ax[0, 1].imshow(channel1[f1]/channel2_registered_SR[f1])
ax[0, 2].imshow(channel1[f1]/channel2_registered_SITK[f1])
ax[0, 3].imshow(channel1[f1]/channel2_registered_SITK_framebyframe[f1])
ax[1, 0].imshow(channel1[f2]/channel2[f2])
ax[1, 1].imshow(channel1[f2]/channel2_registered_SR[f2])
ax[1, 2].imshow(channel1[f2]/channel2_registered_SITK[f2])
ax[1, 3].imshow(channel1[f2]/channel2_registered_SITK_framebyframe[f2])
ax[2, 0].imshow(channel1[f3]/channel2[f3])
ax[2, 1].imshow(channel1[f3]/channel2_registered_SR[f3])
ax[2, 2].imshow(channel1[f3]/channel2_registered_SITK[f3])
ax[2, 3].imshow(channel1[f3]/channel2_registered_SITK_framebyframe[f3])

ax[0, 0].set_title("original")
ax[0, 1].set_title("SR")
ax[0, 2].set_title("SITK")
ax[0, 3].set_title("SITK f by f")

#ax[0, 0].text(-0.5, 0.5, 'test')
ax[0, 0].text(-0.5, 0.5, 'frame '+str(f1+1),
        horizontalalignment='left',
        verticalalignment='center',
        rotation='vertical',
        transform=ax[0,0].transAxes)
ax[1, 0].text(-0.5, 0.5, 'frame '+str(f2+1),
              horizontalalignment='left',
              verticalalignment='center',
              rotation='vertical',
              transform=ax[1,0].transAxes)
ax[2, 0].text(-0.5, 0.5, 'frame '+str(f3+1),
              horizontalalignment='left',
              verticalalignment='center',
              rotation='vertical',
              transform=ax[2,0].transAxes)



for ax_i in ax.reshape(-1):
    ax_i.axis('off')

fig.tight_layout()

plt.show()
