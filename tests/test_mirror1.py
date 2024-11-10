import pytest
from src.researchme import Mirror1

class TestMirror1:
    @pytest.fixture
    def mirror(self):
        return Mirror1()

    def test_search_fields(self, mirror):
        # Test with all fields set to True
        fields = mirror.search_fields(
            title=True,
            authors=True,
            series=True,
            year=True,
            publisher=True,
            isbn=True
        )
        assert len([f for f in fields if f]) == 6
        assert 'columns%5B%5D=t' in fields
        assert 'columns%5B%5D=a' in fields

    def test_topics(self, mirror):
        # Test with all topics set to True
        topics = mirror.search_categories(
            libgen=True,
            comics=True,
            fiction=True
        )
        assert 'topics%5B%5D=l' in topics
        assert 'topics%5B%5D=c' in topics
        assert 'topics%5B%5D=f' in topics

    def test_filtered(self, mirror):
        # Test filtering metadata
        sample_metadata = [
            {
                'title': 'Python Programming',
                'author': 'John Doe',
                'language': 'English',
                'year': '2023',
                'publisher': 'Tech Books'
            },
            {
                'title': 'Java Programming',
                'author': 'Jane Smith',
                'language': 'English',
                'year': '2022',
                'publisher': 'Code Press'
            }
        ]

        # Test filtering by title
        filtered = mirror.filtered(sample_metadata, title='Python')
        assert len(filtered) == 1
        assert filtered[0]['title'] == 'Python Programming'

        # Test filtering by multiple criteria
        filtered = mirror.filtered(
            sample_metadata,
            language='English',
            year='2023'
        )
        assert len(filtered) == 1
        assert filtered[0]['year'] == '2023'

    @pytest.mark.integration
    def test_search_integration(self, mirror):
        # Note: This is an integration test that hits the actual API
        mirror.search('Python Programming', max_results=25)
        metadata = mirror.get_metadata(max_entries=5)

        assert isinstance(metadata, list)
        if metadata:  # If results were found
            assert len(metadata) <= 5
            assert all(isinstance(item, dict) for item in metadata)
            required_keys = {'title', 'author', 'publisher', 'year', 'language'}
            assert all(required_keys.issubset(item.keys()) for item in metadata)