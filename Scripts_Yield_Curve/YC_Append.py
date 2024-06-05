""" Created on 03-09-2024 06:21:18 @author: ripintheblue """
import fatwoman_log_setup
from fatwoman_log_setup import script_end_log
from fatwoman_dir_setup import YC_Quantlib_Plot, YC_Scipy_Plot, YC_Appended_Plot
from scipy.interpolate import CubicSpline
import socket
import logging
import matplotlib
if socket.gethostname() != 'ripintheblue': matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.image as mpimg
sns.set()

# print('Running YCAppend')

image_paths = [YC_Scipy_Plot, YC_Quantlib_Plot]

# Create a figure and a set of subplots
fig, axs = plt.subplots(len(image_paths),1)

# Load and display each image
for ax, img_path in zip(axs, image_paths):
    print('Reading %s' %img_path)
    logging.info('Reading %s' %img_path)
    img = mpimg.imread(img_path)
    ax.imshow(img)
    ax.axis('off')  # Hide axes ticks

plt.tight_layout()
print('Saving %s' %YC_Appended_Plot)
logging.info('Saving %s' %YC_Appended_Plot)
plt.savefig(YC_Appended_Plot, bbox_inches='tight', dpi=300)

script_end_log()
