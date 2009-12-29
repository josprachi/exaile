import unittest

import mox
import gio

import xl.collection
import xl.trax.search
import xl.trax.track
import xl.trax.util

from tests.xl.trax import test_data


def test_is_valid_track_valid():
    for track in test_data.TEST_TRACKS:
        if track.endswith('.aac'):
            continue
        assert xl.trax.util.is_valid_track(track), track

def test_is_valid_track_invalid():
    assert not xl.trax.util.is_valid_track('/')
    assert not xl.trax.util.is_valid_track('/tmp')
    assert not xl.trax.util.is_valid_track(__file__)
    assert not xl.trax.util.is_valid_track('http:///tmp')

class TestGetTracksFromUri(unittest.TestCase):
    class DummyClass:
        def __init__(self, parent, retval):
            self.parent = parent
            self.retval = retval
        def query_info(self, value):
            self.parent.assertEqual(value, 'standard::type')
            return self
        def get_file_type(self):
            return self.retval

    def setUp(self):
        self.mox = mox.Mox()
    
    def tearDown(self):
        self.mox.UnsetStubs()

    def get_anything(self, type, loc):
        anything = self.mox.CreateMockAnything()
        anything.query_info('standard::type').AndReturn(anything)
        if type == 'f':
            anything.get_file_type().AndReturn(gio.FILE_TYPE_REGULAR)
        elif type == 'd':
            anything.get_file_type().AndReturn(gio.FILE_TYPE_DIRECTORY)
        return anything

    def test_single(self):
        loc = '/tmp/foo'
        self.mox.StubOutWithMock(gio, 'File')
        f_anything = self.get_anything('f', loc)
        gio.File(loc).AndReturn(f_anything)
        self.mox.ReplayAll()
        self.assertEqual(xl.trax.util.get_tracks_from_uri(loc),
                [xl.trax.track.Track(loc)])
        self.mox.VerifyAll()

    def test_directory(self):
        loc = '/tmp/foo'
        retval = ['foo', 'bar', 'baz']
        # Gio call to find type
        self.mox.StubOutWithMock(gio, 'File')
        d_anything = self.get_anything('d', loc)
        gio.File(loc).AndReturn(d_anything)

        # scanning
        self.mox.StubOutWithMock(xl.collection.Library, 'rescan')
        xl.collection.Library.rescan()
        self.mox.StubOutWithMock(xl.collection.Collection, 'get_tracks')
        xl.collection.Collection.get_tracks().AndReturn(retval)

        self.mox.ReplayAll()
        xl.trax.util.get_tracks_from_uri(loc)
        self.mox.VerifyAll()

class TestSortTracks(unittest.TestCase):

    def setUp(self):
        self.tracks = [xl.trax.track.Track(url) for url in
                    ('/tmp/foo', '/tmp/bar', '/tmp/baz')]
        for track, val in zip(self.tracks, 'aab'):
            track.set_tag_raw('artist', val)
        for track, val in zip(self.tracks, '212'):
            track.set_tag_raw('discnumber', val)
        self.fields = ('artist', 'discnumber')
        self.result = [self.tracks[1], self.tracks[0], self.tracks[2]]

    def test_invalid(self):
        # This test is purposely created as a reminder to change the docstring
        # on sort_tracks. Please remove this tests after that is done
        # It should not be ``iterable`` for fields parameter
        xl.trax.util.sort_tracks((x for x in ('foo', 'bar')), [], False)

    def test_sorted(self):
        self.assertEqual(xl.trax.util.sort_tracks(self.fields,
            self.tracks), self.result)

    def test_reversed(self):
        self.assertEqual(xl.trax.util.sort_tracks(self.fields,
            self.tracks, True), list(reversed(self.result)))

class TestSortResultTracks(unittest.TestCase):

    def setUp(self):
        tracks = [xl.trax.track.Track(url) for url in
                    ('/tmp/foo', '/tmp/bar', '/tmp/baz')]
        for track, val in zip(tracks, 'aab'):
            track.set_tag_raw('artist', val)
        for track, val in zip(tracks, '212'):
            track.set_tag_raw('discnumber', val)
        self.tracks = [xl.trax.search.SearchResultTrack(track)
                for track in tracks]
        self.fields = ('artist', 'discnumber')
        self.result = [self.tracks[1], self.tracks[0], self.tracks[2]]

    def test_sorted(self):
        self.assertEqual(xl.trax.util.sort_result_tracks(self.fields,
            self.tracks), self.result)

    def test_reversed(self):
        self.assertEqual(xl.trax.util.sort_result_tracks(self.fields,
            self.tracks, True), list(reversed(self.result)))

