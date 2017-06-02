# -*- coding: utf-8 -*-
import numpy as np
import tensorflow as tf


class ImagePatch(object):
    """
    This class defines the output element of an image sampler and
    the element in the input buffer.


    It assumes all images have same length in all spatial dims
    i.e., image_shape = [image_size] * spatial_rank
    and full_image_shape = [image_spatial_shape] + [number_of_modalities]
    """

    def __init__(self,
                 image_shape,
                 info_length,
                 label_shape=None,
                 weight_map_shape=None,
                 image_dtype=tf.float32,
                 label_dtype=tf.int64,
                 weight_map_dtype=tf.float32,
                 num_image_modality=1,
                 num_label_modality=1,
                 num_weight_map=1):

        # shapes
        self._image_shape = image_shape
        self._label_shape = label_shape
        self._weight_map_shape = weight_map_shape
        self._info_length = info_length

        # types
        self._image_dtype = image_dtype
        self._label_dtype = label_dtype
        self._weight_map_dtype = weight_map_dtype

        self._num_image_modality = num_image_modality
        self._num_label_modality = num_label_modality
        self._num_weight_map = num_weight_map

        assert len(set(image_shape)) == 1
        if label_shape is not None:
            assert len(label_shape) == int(np.floor(self.spatial_rank))
            assert len(set(label_shape)) == 1
        if weight_map_shape is not None:
            assert len(weight_map_shape) == int(np.floor(self.spatial_rank))
            assert len(set(weight_map_shape)) == 1

        # actual data
        self._image = None
        self._info = None
        self._label = None
        self._weight_map = None

    @property
    def spatial_rank(self):
        # spatial_rank == 3 for volumetric images
        # spatial_rank == 2 for 2D images
        return 1.0*self._info_length/2.0
        # if self._image_shape[-1] == 1:
        #     return 2.5
        # return len(self._image_shape)

    @property
    def has_labels(self):
        return (self._label_shape is not None) and \
               (self._num_label_modality > 0)

    @property
    def has_weight_maps(self):
        return (self._weight_map_shape is not None) and \
               (self._num_weight_map > 0)

    @property
    def image_size(self):
        # assumes the samples have the same length in all spatial dims
        return set(self._image_shape).pop()

    @property
    def label_size(self):
        if self.has_labels:
            # assumes the samples have the same length in all spatial dims
            return set(self._label_shape).pop()
        return None

    @property
    def weight_map_size(self):
        if self.has_weight_maps:
            # assumes the samples have the same length in all spatial dims
            return set(self._weight_map_shape).pop()
        return None

    @property
    def num_window(self):
        return np.floor(self.spatial_rank)

    @property
    def num_locations(self):
        return np.ceil(self.spatial_rank)

    @property
    def full_informative_image_shape(self):
        spatial_dims = [self.image_size] * self.num_window
        if self.spatial_rank <= 2.5:
            spatial_dims = spatial_dims + [1]
        return spatial_dims + [self._num_image_modality]

    @property
    def full_informative_label_shape(self):
        spatial_dims = [self.label_size] * self.num_window
        if self.spatial_rank <= 2.5:
            spatial_dims = spatial_dims + [1]
        return spatial_dims + [self._num_label_modality]

    @property
    def full_informative_weight_shape(self):
        spatial_dims = [self.weight_map_size] * self.num_window
        if self.spatial_rank <= 2.5:
            spatial_dims = spatial_dims + [1]
        return spatial_dims + [self._num_weight_map]

    @property
    def full_image_shape(self):
        spatial_dims = [self.image_size] * self.num_window
        return spatial_dims + [self._num_image_modality]

    @property
    def full_label_shape(self):
        if self.has_labels:
            # assumes the samples have the same length in all spatial dims
            spatial_dims = [self.label_size] * self.num_window
            return spatial_dims + [self._num_label_modality]
        return None

    @property
    def full_weight_map_shape(self):
        if self.has_weight_maps:
            spatial_dims = [self.weight_map_size] * self.num_window
            return spatial_dims + [self._num_weight_map]
        return None

    @property
    def full_info_shape(self):
        """
        `info` contains the spatial location of a image patch
        it will be used to put the sampled patch back to the original volume
        the first dim: volume id
        the size of the other dims: spatial_rank * 2, indicating starting
        and end point of a patch in each dim
        """
        return [1 + self.spatial_rank * 2]

    def create_placeholders(self):
        """
        The placeholders are defined so that the input buffer knows how
        to initialise an input queue
        """

        placeholders_list = []
        # image (required placeholder)
        image_placeholders = tf.placeholder(
            dtype=self._image_dtype,
            shape=self.full_image_shape,
            name='images')
        placeholders_list.append(image_placeholders)

        # location information (required placeholder)
        # datatype is fixed to tf.int64
        location_info_dtype = tf.int64
        info_placeholders = tf.placeholder(
            dtype=location_info_dtype,
            shape=self.full_info_shape,
            name='info')
        placeholders_list.append(info_placeholders)

        # optional label placeholder
        if self.has_labels:
            label_placeholders = tf.placeholder(
                dtype=self._label_dtype,
                shape=self.full_label_shape,
                name='labels')
            placeholders_list.append(label_placeholders)

        # optional weight_map information
        if self.has_weight_maps:
            weight_map_placeholders = tf.placeholder(
                dtype=self._weight_map_dtype,
                shape=self.full_weight_map_shape,
                name='weightmaps')
            placeholders_list.append(weight_map_placeholders)
        return tuple(placeholders_list)

    ### set the corresponding data of each placeholder
    @property
    def image(self):
        assert self._image is not None
        return self._image

    @property
    def label(self):
        assert self._label is not None
        return self._label

    @property
    def weight_map(self):
        assert self._weight_map is not None
        return self._weight_map

    @property
    def info(self):
        assert self._info is not None
        return self._info

    @image.setter
    def image(self, value):
        assert value.shape == tuple(self.full_image_shape)
        self._image = value

    @info.setter
    def info(self, value):
        assert value.shape == tuple(self.full_info_shape)
        self._info = value

    @label.setter
    def label(self, value):
        assert self.has_labels
        assert value.shape == tuple(self.full_label_shape)
        self._label = value

    @weight_map.setter
    def weight_map(self, value):
        assert self.has_weight_maps
        assert value.shape == tuple(self.full_weight_map_shape)
        self._weight_map = value

    ### end of set the corresponding data of each placeholder

    def set_data(self, subject_id, spatial_loc, img, seg, w_map):

        # TODO:check the colon operator
        self.info = np.array(np.hstack([[subject_id], spatial_loc]),
                             dtype=np.int64)
        assert img is not None

        if self.spatial_rank == 3:
            x_, y_, z_, _x, _y, _z = spatial_loc
            assert _x <= img.data.shape[0]
            assert _y <= img.data.shape[1]
            assert _z <= img.data.shape[2]
            self.image = img.data[x_:_x, y_:_y, z_:_z, :]
            if self.has_labels and (seg is not None):
                diff = self.image_size - self.label_size
                assert diff >= 0  # assumes label_size <= image_size
                x_d, y_d, z_d = (x_ + diff), (y_ + diff), (z_ + diff)
                self.label = \
                    seg.data[x_d: (self.label_size + x_d),
                    y_d: (self.label_size + y_d),
                    z_d: (self.label_size + z_d), :]

            if self.has_weight_maps and (w_map is not None):
                diff = self.image_size - self.weight_map_size
                assert diff >= 0
                x_d, y_d, z_d = (x_ + diff), (y_ + diff), (z_ + diff)
                self.weight_map = \
                    w_map.data[x_d: (self.weight_map_size + x_d),
                    y_d: (self.weight_map_size + y_d),
                    z_d: (self.weight_map_size + z_d), :]

        elif self.spatial_rank == 2:
            x_, y_, _x, _y, = spatial_loc
            assert _x <= img.data.shape[0]
            assert _y <= img.data.shape[1]
            self.image = img.data[x_:_x, y_:_y, 0, :]
            if self.has_labels and (seg is not None):
                diff = self.image_size - self.label_size
                assert diff >= 0  # assumes label_size <= image_size
                x_d, y_d = (x_ + diff), (y_ + diff)
                self.label = \
                    seg.data[x_d: (self.label_size + x_d),
                    y_d: (self.label_size + y_d), 0, :]

            if self.has_weight_maps and (w_map is not None):
                diff = self.image_size - self.weight_map_size
                assert diff >= 0
                x_d, y_d, = (x_ + diff), (y_ + diff)
                self.weight_map = \
                    w_map.data[x_d: (self.weight_map_size + x_d),
                    y_d: (self.weight_map_size + y_d), 0, :]

        elif self.spatial_rank == 2.5:
            x_, y_, z_, _x, _y = spatial_loc
            assert _x <= img.data.shape[0]
            assert _y <= img.data.shape[1]
            assert z_ < img.data.shape[2]
            self.image = img.data[x_:_x, y_:_y, z_, :]
            if self.has_labels and (seg is not None):
                diff = self.image_size - self.label_size
                assert diff >= 0  # assumes label_size <= image_size
                x_d, y_d = (x_ + diff), (y_ + diff)
                self.label = \
                    seg.data[x_d: (self.label_size + x_d),
                    y_d: (self.label_size + y_d),
                    z_ , :]

            if self.has_weight_maps and (w_map is not None):
                diff = self.image_size - self.weight_map_size
                assert diff >= 0
                x_d, y_d = (x_ + diff), (y_ + diff)
                self.weight_map = \
                    w_map.data[x_d: (self.weight_map_size + x_d),
                    y_d : (self.weight_map_size + y_d),
                    z_, :]

    def as_dict(self, placeholders):
        out_list = [self.image, self.info]
        if self.has_labels:
            out_list.append(self.label)
        if self.has_weight_maps:
            out_list.append(self.weight_map)

        assert not any([x is None for x in out_list])
        assert len(out_list) == len(placeholders)
        return {placeholders: tuple(out_list)}

    @property
    def stopping_signal(self):
        return -1 * np.ones(self.full_info_shape)

    def fill_with_stopping_info(self):
        self.info = self.stopping_signal

    def is_stopping_signal(self, info):
        if info is None:
            raise ValueError('wrong data format')
        return np.all(info == self.stopping_signal)