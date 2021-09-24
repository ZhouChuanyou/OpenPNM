import numpy as np
from openpnm.network import GenericNetwork
from openpnm.network.generators import cubic_template, tools
from openpnm.utils import logging
logger = logging.getLogger(__name__)


class CubicTemplate(GenericNetwork):
    r"""
    Simple cubic lattice with arbitrary domain shape specified by a template
    image

    The class creates a standard Cubic network the same shape as the provided
    image, then trims pores from the network that are not in the mask.

    Parameters
    ----------
    template : array_like
        A boolean mask or image defining the desired shape of the domain.  All
        locations in the image that are marked as ``True`` are kept while the
        rest of trimmed to yeild the shape.
    spacing : array_like, optional
        The spacing between pore centers in each direction. If not given, then
        [1, 1, 1] is assumed.
    name : string
        An optional name for the object to help identify it.  If not given,
        one will be generated.
    project : OpenPNM Project object, optional
        Each OpenPNM object must be part of a *Project*.  If none is supplied
        then one will be created and this Network will be automatically
        assigned to it.  To create a *Project* use ``openpnm.Project()``.

    Notes
    -----
    The other arguments are the same as ``Cubic`` except that ``shape`` is
    inferred from the ``template`` image.

    See Also
    --------
    The following methods in ``topotools`` can help generate template images:

    template_cylinder_annulus
    template_sphere_shell

    """

    def __init__(self, template, spacing=[1, 1, 1], **kwargs):
        super().__init__(**kwargs)
        net = cubic_template(template=template, spacing=spacing)
        net = tools.add_all_label(net)
        self.update(net)
