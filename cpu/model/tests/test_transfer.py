__author__ = 'mdenil'

import numpy as np
import scipy.optimize

import unittest
from cpu import model
from cpu import space

class Softmax(unittest.TestCase):
    def setUp(self):
        # X = ['w', 'f', 'd', 'b']
        # Y = ['d', 'b'] (d = classes)
        w,f,d,b = 2, 3, 5, 10
        self.n_input_dimensions = w*f*d
        self.n_classes = 7

        self.layer = model.transfer.Softmax(
            n_classes=self.n_classes,
            n_input_dimensions=self.n_input_dimensions)

        self.X = np.random.standard_normal(size=(w, f, d, b))
        self.Y = np.random.randint(0, self.n_classes, size=b)
        self.Y = np.equal.outer(np.arange(self.n_classes), self.Y).astype(self.X.dtype)

        self.X_space = space.Space.infer(self.X, ['w', 'f', 'd', 'b'])

        self.meta = {'lengths': np.zeros(b) + w, 'space_below': self.X_space}

        self.cost = model.cost.CrossEntropy()

    def test_fprop(self):
        actual, _, _ = self.layer.fprop(self.X, meta=self.meta)
        expected = np.exp(np.dot(self.layer.W, self.X.reshape((self.n_input_dimensions, -1))) + self.layer.b)
        expected /= np.sum(expected, axis=0)

        assert np.allclose(actual, expected)

    def test_bprop(self):
        def func(x):
            x = x.reshape(self.X.shape)
            Y, meta, fprop_state = self.layer.fprop(x, meta=self.meta)
            c, meta, cost_state = self.cost.fprop(Y, self.Y, meta=meta)
            return c

        def grad(x):
            X = x.reshape(self.X.shape)
            Y, meta, fprop_state = self.layer.fprop(X, self.meta)
            cost, meta, cost_state = self.cost.fprop(Y, self.Y, meta=meta)
            delta, meta = self.cost.bprop(Y, self.Y, meta=meta, fprop_state=cost_state)
            delta, _ = self.layer.bprop(delta, meta=meta, fprop_state=fprop_state)
            return delta.ravel()

        assert scipy.optimize.check_grad(func, grad, self.X.ravel()) < 1e-5

    def test_grad_W(self):
        def func(w):
            self.layer.W = w.reshape(self.layer.W.shape)
            Y, meta, fprop_state = self.layer.fprop(self.X, meta=dict(self.meta))
            c, meta, cost_state = self.cost.fprop(Y, self.Y, meta=meta)
            return c

        def grad(w):
            self.layer.W = w.reshape(self.layer.W.shape)
            Y, meta, fprop_state = self.layer.fprop(self.X, meta=dict(self.meta))
            cost, meta, cost_state = self.cost.fprop(Y, self.Y, meta=meta)
            delta, meta = self.cost.bprop(Y, self.Y, meta=dict(meta), fprop_state=cost_state)
            [grad_W, _] = self.layer.grads(delta, meta=dict(meta), fprop_state=fprop_state)

            return grad_W.ravel()

        assert scipy.optimize.check_grad(func, grad, self.layer.W.ravel()) < 1e-5

    def test_grad_b(self):
        cost = model.cost.CrossEntropy()

        def func(b):
            self.layer.b = b.reshape(self.layer.b.shape)
            Y, meta, fprop_state = self.layer.fprop(self.X, meta=self.meta)
            c, meta, cost_state = cost.fprop(Y, self.Y, meta)
            return c

        def grad(b):
            self.layer.b = b.reshape(self.layer.b.shape)
            Y, meta, fprop_state = self.layer.fprop(self.X, meta=self.meta)
            c, meta, cost_state = cost.fprop(Y, self.Y, meta=meta)
            delta, meta = cost.bprop(Y, self.Y, meta=meta, fprop_state=cost_state)
            [_, grad_b] = self.layer.grads(delta, meta=meta, fprop_state=fprop_state)

            return grad_b.ravel()

        assert scipy.optimize.check_grad(func, grad, self.layer.b.ravel()) < 1e-5



class Bias(unittest.TestCase):
    def setUp(self):
        b,w,f,d = 2, 1, 3, 2

        self.layer = model.transfer.Bias(
            n_feature_maps=f,
            n_input_dims=d)
        # biases default to zero, lets mix it up a bit
        self.layer.b = np.random.standard_normal(size=self.layer.b.shape)

        self.X = np.random.standard_normal(size=(b,w,f,d))
        self.X_space = space.Space.infer(self.X, ['b', 'w', 'f', 'd'])
        self.meta = {'lengths': np.zeros(b) + w, 'space_below': self.X_space}


    def test_fprop(self):
        actual, meta, fprop_state = self.layer.fprop(self.X, meta=dict(self.meta))
        expected = self.X + self.layer.b

        assert np.allclose(actual, expected)

    def test_bprop(self):
        def func(x):
            X = x.reshape(self.X.shape)
            Y, meta, fprop_state = self.layer.fprop(X, meta=dict(self.meta))
            return Y.sum()

        def grad(x):
            X = x.reshape(self.X.shape)
            Y, meta, fprop_state = self.layer.fprop(X, meta=dict(self.meta))
            delta, meta = self.layer.bprop(np.ones_like(Y), meta=dict(meta), fprop_state=fprop_state)
            delta, _ = meta['space_below'].transform(delta, self.X_space.axes)

            return delta.ravel()

        assert scipy.optimize.check_grad(func, grad, self.X.ravel()) < 1e-5

    def test_grad_b(self):
        def func(b):
            self.layer.b = b.reshape(self.layer.b.shape)
            Y, meta, fprop_state = self.layer.fprop(self.X, meta=dict(self.meta))
            return Y.sum()

        def grad(b):
            self.layer.b = b.reshape(self.layer.b.shape)

            Y, meta, fprop_state = self.layer.fprop(self.X, meta=dict(self.meta))
            grads = self.layer.grads(np.ones_like(Y), meta=dict(meta), fprop_state=fprop_state)

            gb = grads[0]

            return gb.ravel()

        assert scipy.optimize.check_grad(func, grad, self.layer.b.ravel()) < 1e-5



class SentenceConvolution(unittest.TestCase):
    def setUp(self):
        b,w,f,d = 2, 20, 2, 2
        kernel_width = 4

        self.layer = model.transfer.SentenceConvolution(
            n_feature_maps=f,
            n_input_dimensions=d,
            kernel_width=kernel_width)

        self.X = np.random.standard_normal(size=(b,w,d))

        self.X_space = space.Space.infer(self.X, ['b', 'w', 'd'])
        self.meta = {'lengths': np.random.randint(1, w, size=b), 'space_below': self.X_space}

        # Using this causes test_grad_W to fail if you forget to flip delta before the convolution when computing
        # the gradient (this is good because if you forget that you're doing it wrong).  If you don't have a mask and
        # just backprop all ones then the test still passes without the flip (i.e. with the wrong gradient).
        self.delta_mask = np.random.uniform(size=(b*d*f, w+kernel_width-1)) > 0.5


    def test_fprop(self):
        self.skipTest('WRITEME')

    def test_bprop(self):
        def func(x):
            X = x.reshape(self.X.shape)
            Y, meta, fprop_state = self.layer.fprop(X, meta=dict(self.meta))
            Y *= self.delta_mask
            return Y.sum()

        def grad(x):
            X = x.reshape(self.X.shape)
            Y, meta, fprop_state = self.layer.fprop(X, meta=dict(self.meta))
            delta, meta = self.layer.bprop(self.delta_mask, meta=dict(meta), fprop_state=fprop_state)
            delta, _ = meta['space_below'].transform(delta, self.X_space.axes)
            return delta.ravel()

        assert scipy.optimize.check_grad(func, grad, self.X.ravel()) < 1e-5

    def test_grad_W(self):
        def func(W):
            self.layer.W = W.reshape(self.layer.W.shape)
            Y, meta, fprop_state = self.layer.fprop(self.X.copy(), meta=dict(self.meta))
            Y *= self.delta_mask
            return Y.sum()

        def grad(W):
            self.layer.W = W.reshape(self.layer.W.shape)

            Y, meta, fprop_state = self.layer.fprop(self.X.copy(), meta=dict(self.meta))
            delta = np.ones_like(Y)
            [grad_W] = self.layer.grads(self.delta_mask, meta=dict(meta), fprop_state=fprop_state)

            return grad_W.ravel()

        assert scipy.optimize.check_grad(func, grad, self.layer.W.ravel()) < 1e-5

