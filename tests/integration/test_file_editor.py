import pytest

from openhands_aci.editor.editor import OHEditor
from openhands_aci.editor.exceptions import (
    EditorToolParameterInvalidError,
    EditorToolParameterMissingError,
    ToolError,
)
from openhands_aci.editor.results import CLIResult, ToolResult


@pytest.fixture
def editor(tmp_path):
    editor = OHEditor()
    # Set up a temporary directory with test files
    test_file = tmp_path / 'test.txt'
    test_file.write_text('This is a test file.\nThis file is for testing purposes.')
    return editor, test_file


def test_view_file(editor):
    editor, test_file = editor
    result = editor(command='view', path=str(test_file))
    assert isinstance(result, CLIResult)
    assert f"Here's the result of running `cat -n` on {test_file}:" in result.output
    assert '1\tThis is a test file.' in result.output
    assert '2\tThis file is for testing purposes.' in result.output


def test_create_file(editor):
    editor, test_file = editor
    new_file = test_file.parent / 'new_file.txt'
    result = editor(command='create', path=str(new_file), file_text='New file content')
    assert isinstance(result, ToolResult)
    assert new_file.exists()
    assert new_file.read_text() == 'New file content'
    assert 'File created successfully' in result.output


def test_str_replace(editor):
    editor, test_file = editor
    result = editor(
        command='str_replace',
        path=str(test_file),
        old_str='test file',
        new_str='sample file',
    )
    assert isinstance(result, CLIResult)
    assert 'The file' in result.output
    assert 'sample file' in test_file.read_text()


def test_str_replace_error_multiple_occurrences(editor):
    editor, test_file = editor
    with pytest.raises(ToolError) as exc_info:
        editor(
            command='str_replace', path=str(test_file), old_str='test', new_str='sample'
        )

    assert 'Multiple occurrences of old_str `test`' in str(exc_info.value)


def test_insert(editor):
    editor, test_file = editor
    result = editor(
        command='insert', path=str(test_file), insert_line=1, new_str='Inserted line'
    )
    assert isinstance(result, CLIResult)
    assert 'Inserted line' in test_file.read_text()


def test_undo_edit(editor):
    editor, test_file = editor
    # Make an edit to be undone
    result = editor(
        command='str_replace',
        path=str(test_file),
        old_str='test file',
        new_str='sample file',
    )
    print(f'output: {result.output}')
    # Undo the edit
    result = editor(command='undo_edit', path=str(test_file))
    print(result.output)
    assert isinstance(result, CLIResult)
    assert 'Last edit to' in result.output
    assert 'test file' in test_file.read_text()  # Original content restored


def test_validate_path_invalid(editor):
    editor, test_file = editor
    invalid_file = test_file.parent / 'nonexistent.txt'
    with pytest.raises(EditorToolParameterInvalidError):
        editor(command='view', path=str(invalid_file))


def test_create_existing_file_error(editor):
    editor, test_file = editor
    with pytest.raises(EditorToolParameterInvalidError):
        editor(command='create', path=str(test_file), file_text='New content')


def test_str_replace_missing_old_str(editor):
    editor, test_file = editor
    with pytest.raises(EditorToolParameterMissingError):
        editor(command='str_replace', path=str(test_file), new_str='sample')


def test_insert_missing_line_param(editor):
    editor, test_file = editor
    with pytest.raises(EditorToolParameterMissingError):
        editor(command='insert', path=str(test_file), new_str='Missing insert line')


def test_undo_edit_no_history_error(editor):
    editor, test_file = editor
    empty_file = test_file.parent / 'empty.txt'
    empty_file.write_text('')
    with pytest.raises(ToolError):
        editor(command='undo_edit', path=str(empty_file))
