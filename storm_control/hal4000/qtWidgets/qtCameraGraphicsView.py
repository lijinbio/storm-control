#!/usr/bin/env python
"""
QGraphicsView customized for displaying camera images.

Hazen 3/17
"""

from PyQt5 import QtCore, QtGui, QtWidgets


class QtCameraGraphicsView(QtWidgets.QGraphicsView):
    """

    """
    newCenter = QtCore.pyqtSignal(int, int)
    newScale = QtCore.pyqtSignal(int)
    
    def __init__(self, parent = None, **kwds):
        kwds["parent"] = parent
        super().__init__(**kwds)

        self.chip_max = 0
        self.center_x = 0
        self.center_y = 0
        self.ctrl_key_down = False
        self.frame_size = 0
        self.max_scale = 8
        self.min_scale = -8
        self.scale = 0
        self.viewport_min = 100

        self.setAcceptDrops(True)
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(0,0,0)))

    def keyPressEvent(self, event):
        if (event.key() == QtCore.Qt.Key_Control):
            self.ctrl_key_down = True
            QtWidgets.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.OpenHandCursor))

    def keyReleaseEvent(self, event):
        if (event.key() == QtCore.Qt.Key_Control):
            self.ctrl_key_down = False
            if not self.drag_mode:
                QtWidgets.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))

    def mousePressEvent(self, event):
        self.center_x = event.x()
        self.center_y = event.y()
        self.newCenter.emit(self.center_x, self.center_y)
        self.centerOn(self.center_x, self.center_y)
        
    def newConfiguration(self, feed_info, feed_parameters):
        """
        This is called when the camera or frame size may have changed.
        """
        self.chip_max = feed_info.getChipMax()

        # Calculate max zoom out.
        self.min_scale = -int(self.chip_max/self.viewport_min) - 1

        # Calculate initial zoom and center position.
        if feed_parameters.get("initialized"):
            self.scale = feed_parameters.get("scale")
            self.center_x = feed_parameters.get("center_x")
            self.center_y = feed_parameters.get("center_y")
        else:
            if (feed_info.getFrameMax() < self.viewport_min):
                self.scale = int(self.viewport_min/feed_info.getFrameMax()) - 1
            else:
                self.scale = -int(feed_info.getFrameMax()/self.viewport_min)
            [self.center_x, self.center_y] = feed_info.frameCenter()
            feed_parameters.set("initialized", True)

        self.centerOn(self.center_x, self.center_y)
        self.rescale(self.scale)

    def resizeEvent(self, event):
        viewport_rect = self.viewport().contentsRect()
        self.viewport_min = viewport_rect.width() if (viewport_rect.width() < viewport_rect.height())\
                            else viewport_rect.height()

        self.min_scale = -int(self.chip_max/self.viewport_min) - 1
        if (self.scale < self.min_scale):
            self.scale = self.min_scale
        
        super().resizeEvent(event)
        
    def rescale(self, scale):
        """
        Rescale the view so that it looks like we have zoomed in/out.
        """
        if (scale <= self.min_scale) or (scale >= self.max_scale):
            return

        self.scale = scale
        self.newScale.emit(self.scale)

        if (self.scale == 0):
            flt_scale = 1.0
        elif (self.scale > 0):
            flt_scale = float(self.scale + 1)
        else:
            flt_scale = 1.0/(-self.scale + 1)
            
        transform = QtGui.QTransform()
        transform.scale(flt_scale, flt_scale)
        self.setTransform(transform)
        
    def updateScaleRange(self):
        """
        Given the view and camera size, this figures 
        out the range of scales to allow.
        """
        
        # Figure out the minimum dimension of the viewport.
        viewport_rect = self.viewport().contentsRect()
        viewport_size = viewport_rect.width()
        if (viewport_size > viewport_rect.height()):
            viewport_size = viewport_rect.height()

        # This sets how far we can zoom out (and also the starting size).
        self.min_scale = float(viewport_size)/float(self.frame_size + 10)

        # This sets how far we can zoom in (~32 pixels).
        self.max_scale = float(viewport_size)/32.0

        # For those really small cameras.
        if (self.max_scale < self.min_scale):
            self.max_scale = 2.0 * self.min_scale

        if (self.view_scale < self.min_scale):
            self.view_scale = self.min_scale

        if (self.view_scale > self.max_scale):
            self.view_scale = self.max_scale

        print(self.frame_size, viewport_size, self.min_scale, self.max_scale)

    def wheelEvent(self, event):
        """
        Zoom in/out with the mouse wheel.
        """
        if not event.angleDelta().isNull():
            if (event.angleDelta().y() > 0):
                self.rescale(self.scale + 1)
            else:
                self.rescale(self.scale - 1)
            event.accept()