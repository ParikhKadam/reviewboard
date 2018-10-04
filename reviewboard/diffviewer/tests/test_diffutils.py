    _PATCH_GARBAGE_INPUT,
from reviewboard.diffviewer.errors import PatchError
    def test_empty_parent_diff_old_patch(self):
        """Testing get_original_file with an empty parent diff with patch(1)
        that does not accept empty diffs
        """
        # Older versions of patch will choke on an empty patch with a "garbage
        # input" error, but newer versions will handle it just fine. We stub
        # out patch here to always fail so we can test for the case of an older
        # version of patch without requiring it to be installed.
        def _patch(diff, orig_file, filename, request=None):
            raise PatchError(
                filename,
                _PATCH_GARBAGE_INPUT,
                orig_file,
                'tmp123-new',
                b'',
                None)

        self.spy_on(patch, call_fake=_patch)

                request=self.request,
                encoding_list=['ascii'])

    def test_empty_parent_diff_new_patch(self):
        """Testing get_original_file with an empty parent diff with patch(1)
        that does accept empty diffs
        """
        filediff = (
            FileDiff.objects
            .select_related('parent_diff_hash',
                            'diffset',
                            'diffset__repository',
                            'diffset__repository__tool')
            .get(dest_file='corge',
                 dest_detail='f248ba3',
                 commit_id=3)
        )

        # FileDiff creation will set the _IS_PARENT_EMPTY flag.
        del filediff.extra_data[FileDiff._IS_PARENT_EMPTY_KEY]
        filediff.save(update_fields=('extra_data',))

        # Newer versions of patch will allow empty patches. We stub out patch
        # here to always fail so we can test for the case of a newer version
        # of patch without requiring it to be installed.
        def _patch(diff, orig_file, filename, request=None):
            # This is the only call to patch() that should be made.
            self.assertEqual(diff,
                             b'diff --git a/corge b/corge\n'
                             b'new file mode 100644\n'
                             b'index 0000000..e69de29\n')
            return orig_file

        self.spy_on(patch, call_fake=_patch)

        with self.assertNumQueries(0):
            orig = get_original_file(
                filediff=filediff,
                request=self.request,
                encoding_list=['ascii'])

        self.assertEqual(orig, b'')

        # Refresh the object from the database with the parent diff attached
        # and then verify that re-calculating the original file does not cause
        # additional queries.
        filediff = (
            FileDiff.objects
            .select_related('parent_diff_hash')
            .get(pk=filediff.pk)
        )

        with self.assertNumQueries(0):
            orig = get_original_file(
                filediff=filediff,
                request=self.request,