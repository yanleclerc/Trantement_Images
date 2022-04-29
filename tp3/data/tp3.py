import hashlib
import random
import numpy as np
from scipy.ndimage import gaussian_filter
from skimage.util import random_noise
from skimage.transform import warp, SimilarityTransform



__all__ = ['JamesWebbSimulator']


class JamesWebbSimulator(object):
    nb_mirrors = 5
    noise_level = 0.001
    radius_range = 128
    piston_min = 1
    piston_max = 9  
    def __init__(self, code_permanent: str):
        """Simulateur du télescope spatial James-Webb
        Parameters
        ----------
        code_permanent: str
            Une chaîne de caractère contenant votre code permanent. Utilisé pour obtenir l'état initial du télescope.
        """
        self.seed = int(hashlib.sha256(code_permanent.encode('utf-8')).hexdigest(), 16) % 10**4 
        self.telescope_ready = False
        self.reset()

    def reset(self):
        """Ré-initialise le télescope. Annule tous les déplacements de miroirs et retire les corrections appliquées."""
        random.seed(self.seed) # Initialisation du générateur de nombre aléatoire
        self._psf_params = [None] * self.nb_mirrors
        self.radius_bias = [0]*self.nb_mirrors
        self.radius = [0]*self.nb_mirrors
        self.piston = [0]*self.nb_mirrors
        self.piston_bias = [0]*self.nb_mirrors
        for i in range(self.nb_mirrors):
            this_params = {}
            this_params['radius'] = random.uniform(0, self.radius_range)
            this_params['angle'] = random.uniform(0, np.pi * 2)
            this_params['piston'] = random.randint(self.piston_min, self.piston_max)
            self._psf_params[i] = this_params

        random.seed() # Release random seed
        self.telescope_ready = True

    def set_mirror_correction(self, mirror_id: int, bias: float):
        """Configure la correction pour une miroir donné.txt
        Parameters
        ----------
        mirror_id: int
            Indice entier du miroir à corriger
        bias: float
            Valeur de la correction, en pixel.
        """
        self.radius_bias[mirror_id] = bias
        
    def move_mirror_by(self, mirror_id: int, amount: float):
        """Déplace un miroir d'une certaine distance
        Parameters
        ----------
        mirror_id: int
            Indice entier du miroir à déplacer
        amount: float
            Déplacement à effectuer (en pixel)
        """
        self.radius[mirror_id] += amount

    def simulate(self, image: np.ndarray):
        """Simule une capture d'image avec notre télescope
        Parameters
        ----------
        image: np.ndarray
            Image en tons de gris représentant la portion du ciel vers laquel notre télescope pointe
        Returns
        -------
            Image acquise par notre microscope (simulation)
        """
        assert image.ndim == 2, "Image must be a 2D numpy array"

        if not(self.telescope_ready):
            self.reset()

        # Normalize 
        source = (image.astype(float) - image.min()) / (image.max() - image.min())

        # Generate synthetic image
        output = np.zeros_like(source)
        for i in range(self.nb_mirrors):
            # Get radius and piston
            radius = self.radius[i] + self._psf_params[i]['radius'] + self.radius_bias[i]
            piston = np.abs(self.piston[i] + self._psf_params[i]['piston'] + self.piston_bias[i])
            angle = self._psf_params[i]['angle']

            # Translation
            tr = radius * np.cos(angle)
            tc = radius * np.sin(angle)

            # Apply shift
            this_output = warp(source, SimilarityTransform(translation=(tr,tc)), mode='wrap')

            # Apply PSF
            this_output = gaussian_filter(this_output, piston)

            # Add noise
            this_output = random_noise(this_output, mode='gaussian', var=self.noise_level)
            output += this_output

        # Normalize the output
        output = (output.astype(float) - output.min()) / (output.max() - output.min())

        return output
