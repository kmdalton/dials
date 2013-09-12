#
#  Copyright (C) (2013) STFC Rutherford Appleton Laboratory, UK.
#
#  Author: David Waterman.
#
#  This code is distributed under the BSD license, a copy of which is
#  included in the root directory of this package.
#

#### Python and general cctbx imports

from __future__ import division
from scitbx import matrix

#### Import model parameterisations

#from dials.algorithms.refinement.parameterisation.detector_parameters import \
#    DetectorParameterisationSinglePanel
#from dials.algorithms.refinement.parameterisation.beam_parameters import \
#    BeamParameterisationOrientation
#from dials.algorithms.refinement.parameterisation.crystal_parameters import \
#    CrystalOrientationParameterisation, CrystalUnitCellParameterisation
from cctbx.array_family import flex
from dials_refinement_helpers_ext import *

class PredictionParameterisation(object):
    '''
    Abstract interface for a class that groups together model parameterisations
    relating to diffraction geometry and provides:

    * A list of all free parameters concatenated from each of the models, with a
      getter and setter method that delegates to the contained models
    * Derivatives of the reflection prediction equation with respect to each of
      these free parameters

    Derived classes determine whether the reflection prediction equation is
    expressed in detector space (X, Y, phi) or orthogonalised reciprocal space.

    It is assumed that the provided model parameterisations will be one of four
    types:

    * Detector parameterisation
    * Beam parameterisation
    * Crystal orientation parameterisation
    * Crystal unit cell parameterisation

    One of each must be supplied, which could be satisfied by a dummy class if
    no parameterisation is desired for some model.

    We also need access to the underlying models that are parameterised. The
    model parameterisation objects do not provide access to these models:
    it is not their job to do so. Instead we construct this object with direct
    access to each of the models. So, we also need each of:

    * A detector model (single point of reference for every sensor in the
      experiment)
    * A beam model
    * A crystal model
    * A goniometer model (not yet parameterised, but required for the equations)

    A class implementing PredictionParameterisation is used by a Refinery
    object directly, which takes the list of parameters, and indirectly via a
    Target function object, which takes the list of derivatives and composes the
    derivatives of a Target function from them.
    '''

    def __init__(self,
                 detector_model,
                 beam_model,
                 crystal_model,
                 goniometer_model,
                 detector_parameterisations = None,
                 beam_parameterisations = None,
                 xl_orientation_parameterisations = None,
                 xl_unit_cell_parameterisations = None):

        # References to the underlying models
        self._detector = detector_model
        self._beam = beam_model
        self._crystal = crystal_model
        self._gonio = goniometer_model

        # Sanity checks
        #if detector_parameterisations:
        #    for model in detector_parameterisations:
        #        # TODO replace DetectorParameterisationSinglePanel with a
        #        # general multi sensor detector_parameterisation when available
        #        assert isinstance(
        #            model, DetectorParameterisationSinglePanel)
        #
        #if beam_parameterisations:
        #    for model in beam_parameterisations:
        #        assert isinstance(model, BeamParameterisationOrientation)
        #
        #if xl_orientation_parameterisations:
        #    for model in xl_orientation_parameterisations:
        #        assert isinstance(model, CrystalOrientationParameterisation)
        #
        #if xl_unit_cell_parameterisations:
        #    for model in xl_unit_cell_parameterisations:
        #        assert isinstance(model, CrystalUnitCellParameterisation)

        # Keep references to all parameterised models
        self._detector_parameterisations = detector_parameterisations
        self._beam_parameterisations = beam_parameterisations
        self._xl_orientation_parameterisations = \
            xl_orientation_parameterisations
        self._xl_unit_cell_parameterisations = \
            xl_unit_cell_parameterisations

        self._length = self._len()

    def _len(self):
        length = 0
        if self._detector_parameterisations:
            for model in self._detector_parameterisations:
                length += model.num_free()

        if self._beam_parameterisations:
            for model in self._beam_parameterisations:
                length += model.num_free()

        if self._xl_orientation_parameterisations:
            for model in self._xl_orientation_parameterisations:
                length += model.num_free()

        if self._xl_unit_cell_parameterisations:
            for model in self._xl_unit_cell_parameterisations:
                length += model.num_free()

        return length

    def __len__(self):
        return self._length

    def get_param_vals(self):
        '''return a concatenated list of parameters from each of the components
        in the global model'''

        global_p_list = []
        if self._detector_parameterisations:
            det_plists = [x.get_param_vals() for x in self._detector_parameterisations]
            params = [x for l in det_plists for x in l]
            global_p_list.extend(params)

        if self._beam_parameterisations:
            src_plists = [x.get_param_vals() for x in self._beam_parameterisations]
            params = [x for l in src_plists for x in l]
            global_p_list.extend(params)

        if self._xl_orientation_parameterisations:
            xlo_plists = [x.get_param_vals() for x
                          in self._xl_orientation_parameterisations]
            params = [x for l in xlo_plists for x in l]
            global_p_list.extend(params)

        if self._xl_unit_cell_parameterisations:
            xluc_plists = [x.get_param_vals() for x
                           in self._xl_unit_cell_parameterisations]
            params = [x for l in xluc_plists for x in l]
            global_p_list.extend(params)

        return global_p_list

    def get_param_names(self):
        '''Return a list of the names of parameters in the order they are
        concatenated. Useful for output to log files and debugging.'''
        param_names = []
        if self._detector_parameterisations:
            det_param_name_lists = [x.get_param_names() for x in \
                               self._detector_parameterisations]
            names = ["Detector%d" % i + x for i, l \
                     in enumerate(det_param_name_lists) for x in l]
            param_names.extend(names)

        if self._beam_parameterisations:
            src_param_name_lists = [x.get_param_names() for x in \
                               self._beam_parameterisations]
            params = ["Source%d" % i + x for i, l \
                      in enumerate(src_param_name_lists) for x in l]
            param_names.extend(params)

        if self._xl_orientation_parameterisations:
            xlo_param_name_lists = [x.get_param_names() for x
                          in self._xl_orientation_parameterisations]
            params = ["Crystal%d" % i + x for i, l \
                      in enumerate(xlo_param_name_lists) for x in l]
            param_names.extend(params)

        if self._xl_unit_cell_parameterisations:
            xluc_param_name_lists = [x.get_param_names() for x
                           in self._xl_unit_cell_parameterisations]
            params = ["Crystal%d" % i + x for i, l \
                      in enumerate(xluc_param_name_lists) for x in l]
            param_names.extend(params)

        return param_names

    def set_param_vals(self, vals):
        '''Set the parameter values of the contained models to the values in
        vals. This list must be of the same length as the result of
        get_param_vals and must contain the parameter values in the same order!
        This order is to be maintained by any sensible refinement engine.'''

        assert len(vals) == len(self)
        it = iter(vals)

        if self._detector_parameterisations:
            for model in self._detector_parameterisations:
                tmp = [it.next() for i in range(model.num_free())]
                model.set_param_vals(tmp)

        if self._beam_parameterisations:
            for model in self._beam_parameterisations:
                tmp = [it.next() for i in range(model.num_free())]
                model.set_param_vals(tmp)

        if self._xl_orientation_parameterisations:
            for model in self._xl_orientation_parameterisations:
                tmp = [it.next() for i in range(model.num_free())]
                model.set_param_vals(tmp)

        if self._xl_unit_cell_parameterisations:
            for model in self._xl_unit_cell_parameterisations:
                tmp = [it.next() for i in range(model.num_free())]
                model.set_param_vals(tmp)

    def prepare(self):
        '''Cache required quantities that are not dependent on hkl'''

        # Note, the reflection prediction code should be improved to also
        # provide detector + sensor numbers for each prediction, so that we can
        # have multiple sensor parameterisations and only calculate derivatives
        # for the one sensor that the ray does in fact intersect. We then need
        # a way to look up, from a detector + sensor number, which detector
        # parameterisation object refers to that sensor. Ideally this would be
        # done without requiring a search through all of
        # self._detector_parameterisations each time.
        #
        # For now, assume there is only one sensor, and it is parameterised by
        # the first entry in self._detector_parameterisations.

        ### Obtain various quantities of interest from the experimental model

        # Here we irrevocably choose the Panel that this reflection intersects,
        # currently hard-coding it to the first (only) Panel.
        self._D = matrix.sqr(self._detector[0].get_D_matrix())
        self._s0 = matrix.col(self._beam.get_s0())
        self._U = self._crystal.get_U()
        self._B = self._crystal.get_B()
        self._axis = matrix.col(self._gonio.get_rotation_axis())

    def get_gradients(self, h, s, phi, obs_image_number = None):
        '''
        Calculate gradients of the prediction formula with respect to each
        of the parameters of the contained models, for the reflection with
        scattering vector s.

        To be implemented by a derived class, which determines the space of the
        prediction formula (e.g. we calculate dX/dp, dY/dp, dphi/dp for the
        prediction formula expressed in detector space, but components of
        d\vec{r}/dp for the prediction formula in reciprocal space

        obs_image_number included to match the interface of a scan-
        varying version of the class
        '''

        self.prepare()

        return self._get_gradients_core(h, s, phi)

    def get_multi_gradients(self, match_list):
        '''
        perform the functionality of get_gradients but for a list of many
        reflections in one call in the form of a list of ObsPredMatch objects
        (see target.py). The advantage of this is that prepare needs only be
        called once.
        '''

        # This is effectively calculating the Jacobian and perhaps should be
        # renamed as such (and returned as a matrix not a list of lists)

        self.prepare()

        return [self._get_gradients_core(m.H, m.Sc, m.Phic) for m in match_list]


class DetectorSpacePredictionParameterisation(PredictionParameterisation):
    '''
    Concrete class that inherits functionality of the
    PredictionParameterisation parent class and provides a detector space
    implementation of the get_gradients function.

    Not yet safe for multiple sensor detectors.
    '''

    def _get_gradients_core(self, h, s, phi):

        '''Calculate gradients of the prediction formula with respect to each
        of the parameters of the contained models, for reflection h with
        scattering vector s that reflects at rotation angle phi. That is,
        calculate dX/dp, dY/dp and dphi/dp'''

        ### Calculate various quantities of interest for this reflection

        R = self._axis.axis_and_angle_as_r3_rotation_matrix(phi)

        # pv is the 'projection vector' for the reflection s.
        s = matrix.col(s)
        pv = self._D * s
        # r is the reciprocal lattice vector, in the lab frame
        r = R * self._U * self._B * h

        # All of the derivatives of phi have a common denominator, given by
        # (e X r).s0, where e is the rotation axis. Calculate this once, here.
        e_X_r = self._axis.cross(r)
        e_r_s0 = (e_X_r).dot(self._s0)

        try:
            assert abs(e_r_s0) > 1.e-6
        except AssertionError as e:
            print "(e X r).s0 too small:", e_r_s0
            print "for reflection", h
            print "with scattering vector", s
            print "where r =", r
            print "e =",matrix.col(self._gonio.get_rotation_axis())
            print "s0 =",self._s0
            print "U =",self._U
            print "this reflection forms angle with the equatorial plane normal:"
            vecn = self._s0.cross(self._axis).normalize()
            print s.accute_angle(vecn)
            raise e
        # FIXME This is potentially dangerous! e_r_s0 -> 0 when the rotation
        # axis, beam vector and relp are coplanar. This occurs when a reflection
        # just touches the Ewald sphere. The derivatives of phi go to infinity
        # because any change moves it off this one position of grazing
        # incidence. How best to deal with this?

        ### Work through the parameterisations, calculating their contributions
        ### to derivatives d[pv]/dp and d[phi]/dp

        # Set up the lists of derivatives
        dpv_dp = []
        dphi_dp = []

        # Calculate derivatives of pv wrt each parameter of the FIRST detector
        # parameterisation only. All derivatives of phi are zero for detector
        # parameters
        if self._detector_parameterisations:
            self._detector_derivatives(dpv_dp, dphi_dp, pv)

        # Calc derivatives of pv and phi wrt each parameter of each beam
        # parameterisation that is present.
        if self._beam_parameterisations:
            self._beam_derivatives(dpv_dp, dphi_dp, r, e_X_r, e_r_s0)

        # Calc derivatives of pv and phi wrt each parameter of each crystal
        # orientation parameterisation that is present.
        if self._xl_orientation_parameterisations:
            self._xl_orientation_derivatives(dpv_dp, dphi_dp, R, h, s, \
                                             e_X_r, e_r_s0)

        # Now derivatives of pv and phi wrt each parameter of each crystal unit
        # cell parameterisation that is present.
        if self._xl_unit_cell_parameterisations:
            self._xl_unit_cell_derivatives(dpv_dp, dphi_dp, R, h, s, \
                                             e_X_r, e_r_s0)

        # calculate positional derivatives from d[pv]/dp
        pos_grad = [self._calc_dX_dp_and_dY_dp_from_dpv_dp(pv, e) for e in dpv_dp]
        dX_dp, dY_dp = zip(*pos_grad)

        return zip(dX_dp, dY_dp, dphi_dp)

    def _detector_derivatives(self, dpv_dp, dphi_dp, pv):

        '''helper function to extend the derivatives lists by
        derivatives of the detector parameterisations'''
        for idet, det in enumerate(self._detector_parameterisations):

            # Only work for the first detector parameterisation
            if idet == 0:
                dd_ddet_p = det.get_ds_dp()

                # Copy to a flex array of 3*3 matrices
                dd_ddet_p_temp = flex_mat3_double(len(dd_ddet_p))
                for i, dd in enumerate(dd_ddet_p):
                    dd_ddet_p_temp[i] = dd.elems
                dd_ddet_p = dd_ddet_p_temp

                # Calc derivative of pv wrt detector params
                dpv_ddet_p = detector_pv_derivative(
                                self._D, dd_ddet_p, pv)

            # For any other detector parameterisations, set derivatives
            # to zero
            else:
                dpv_ddet_p = [matrix.col((0., 0., 0.))] * len(dd_ddet_p)

            # Derivatives of phi wrt detector params are all zero
            dphi_ddet_p = [0.] * len(dd_ddet_p)

            dpv_dp.extend(dpv_ddet_p)
            dphi_dp.extend(dphi_ddet_p)

            return

    def _beam_derivatives(self, dpv_dp, dphi_dp, r, e_X_r, e_r_s0):

        '''helper function to extend the derivatives lists by
        derivatives of the beam parameterisations'''

        for src in self._beam_parameterisations:
            ds0_dsrc_p = src.get_ds_dp()

            # Calc derivative of phi wrt beam params
            dphi_dsrc_p = beam_phi_derivative(
                                r, flex.vec3_double(ds0_dsrc_p), e_r_s0)

            # Calc derivative of pv wrt beam params
            dpv_dsrc_p = beam_pv_derivative(
                                self._D, e_X_r, dphi_dsrc_p,
                                flex.vec3_double(ds0_dsrc_p))

            dpv_dp.extend(dpv_dsrc_p)
            dphi_dp.extend(dphi_dsrc_p)

            return

    def _xl_orientation_derivatives(self, dpv_dp, dphi_dp, R, h, s, \
                                    e_X_r, e_r_s0):

        '''helper function to extend the derivatives lists by
        derivatives of the crystal orientation parameterisations'''

        for xlo in self._xl_orientation_parameterisations:
            dU_dxlo_p = xlo.get_ds_dp()

            # Calc derivatives of r wrt crystal orientation params
            h2 = (int(h[0]), int(h[1]), int(h[2]))
            dr_dxlo_p = crystal_orientation_r_derivative(
                            R.elems, flex_mat3_double(dU_dxlo_p),
                            self._B.elems, h2)

            # Calc derivatives of phi wrt crystal orientation params
            dphi_dxlo_p = crystal_orientation_phi_derivative(
                                flex.vec3_double(dr_dxlo_p),
                                s, e_r_s0)

            # Calc derivatives of pv wrt crystal orientation params
            dpv_dxlo_p = crystal_orientation_pv_derivative(
                                self._D.elems, dr_dxlo_p,
                                e_X_r.elems, dphi_dxlo_p)

            dpv_dp.extend(dpv_dxlo_p)
            dphi_dp.extend(dphi_dxlo_p)

        return

    def _xl_unit_cell_derivatives(self, dpv_dp, dphi_dp, R, h, s, \
                                    e_X_r, e_r_s0):

        for xluc in self._xl_unit_cell_parameterisations:
            dB_dxluc_p = xluc.get_ds_dp()

            # Calc derivatives of r wrt crystal unit cell params
            h2 = (int(h[0]), int(h[1]), int(h[2]))
            dr_dxluc_p = crystal_cell_r_derivative(
                            R.elems, self._U.elems,
                            flex_mat3_double(dB_dxluc_p), h2)

            # Calc derivatives of phi wrt crystal unit cell params
            dphi_dxluc_p = crystal_cell_phi_derivative(
                                dr_dxluc_p, s, e_r_s0)

            # Calc derivatives of pv wrt crystal unit cell params
            dpv_dxluc_p = crystal_cell_pv_derivative(
                                self._D.elems, dr_dxluc_p,
                                e_X_r.elems, dphi_dxluc_p)

            dpv_dp.extend(dpv_dxluc_p)
            dphi_dp.extend(dphi_dxluc_p)

        return

    def _calc_dX_dp_and_dY_dp_from_dpv_dp(self, pv, der):
        '''helper function to calculate positional derivatives from dpv_dp using
        the quotient rule'''
        u = pv[0]
        v = pv[1]
        w = pv[2]
        w2 = w**2

        du_dp = der[0]
        dv_dp = der[1]
        dw_dp = der[2]

        dX_dp = du_dp / w - u * dw_dp / w2
        dY_dp = dv_dp / w - v * dw_dp / w2

        return dX_dp, dY_dp

class DetectorSpacePredictionParameterisation_py(DetectorSpacePredictionParameterisation):

    '''Python version, overloading functions to calc derivatives only.
    Slow, but somewhat easier to read.'''

    def _detector_derivatives(self, dpv_dp, dphi_dp, pv):

        '''helper function to extend the derivatives lists by
        derivatives of the detector parameterisations'''

        for idet, det in enumerate(self._detector_parameterisations):
            if idet == 0:
                dd_ddet_p = det.get_ds_dp()
                dpv_ddet_p = [- self._D * (dd_ddet_p[i]) * pv for i
                                 in range(len(dd_ddet_p))]
            else:
                dpv_ddet_p = [matrix.col((0., 0., 0.))] * len(dd_ddet_p)

            dphi_ddet_p = [0.] * len(dd_ddet_p)

            dpv_dp.extend(dpv_ddet_p)
            dphi_dp.extend(dphi_ddet_p)

        return

    def _beam_derivatives(self, dpv_dp, dphi_dp, r, e_X_r, e_r_s0):

        '''helper function to extend the derivatives lists by
        derivatives of the beam parameterisations'''

        for src in self._beam_parameterisations:
            ds0_dsrc_p = src.get_ds_dp()
            dphi_dsrc_p = [- r.dot(ds0_dsrc_p[i]) / e_r_s0 for i
                              in range(len(ds0_dsrc_p))]
            dpv_dsrc_p = [self._D * (e_X_r * dphi_dsrc_p[i] + ds0_dsrc_p[i]) for i in range(len(ds0_dsrc_p))]

            dpv_dp.extend(dpv_dsrc_p)
            dphi_dp.extend(dphi_dsrc_p)

            return

    def _xl_orientation_derivatives(self, dpv_dp, dphi_dp, R, h, s, \
                                    e_X_r, e_r_s0):

        '''helper function to extend the derivatives lists by
        derivatives of the crystal orientation parameterisations'''

        for xlo in self._xl_orientation_parameterisations:
            dU_dxlo_p = xlo.get_ds_dp()

            dr_dxlo_p = [R * dU_dxlo_p[i] * self._B * h for i in range(len(dU_dxlo_p))]

            dphi_dxlo_p = [- der.dot(s) / e_r_s0 for der in dr_dxlo_p]

            dpv_dxlo_p = [self._D * (dr_dxlo_p[i] + e_X_r * dphi_dxlo_p[i]) for i in range(len(dphi_dxlo_p))]

            dpv_dp.extend(dpv_dxlo_p)
            dphi_dp.extend(dphi_dxlo_p)

        return

    def _xl_unit_cell_derivatives(self, dpv_dp, dphi_dp, R, h, s, \
                                    e_X_r, e_r_s0):

        '''helper function to extend the derivatives lists by
        derivatives of the crystal unit cell parameterisations'''

        for xluc in self._xl_unit_cell_parameterisations:
            dB_dxluc_p = xluc.get_ds_dp()

            dr_dxluc_p = [R * self._U * dB_dxluc_p[i] * h for i
                              in range(len(dB_dxluc_p))]

            dphi_dxluc_p = [- der.dot(s) / e_r_s0 for der in dr_dxluc_p]

            dpv_dxluc_p = [self._D * (dr_dxluc_p[i] + e_X_r * dphi_dxluc_p[i]) for i in range(len(dr_dxluc_p))]

            dpv_dp.extend(dpv_dxluc_p)
            dphi_dp.extend(dphi_dxluc_p)

        return
