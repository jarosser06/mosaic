# This file contains the fixes needed for test_all_mcp_tools.py

# Fix 1: test_update_note_content (lines 1121-1124)
# OLD:
#         note = Note(
#             content="Original content",
#             privacy_level=PrivacyLevel.PRIVATE,
#         )
#
# NEW:
#         note = Note(
#             text="Original content",
#             entity_type=EntityType.PROJECT,
#             entity_id=1,
#             privacy_level=PrivacyLevel.PRIVATE,
#         )

# Fix 2: test_update_note_privacy_and_tags (lines 1141-1145)
# OLD:
#         note = Note(
#             content="Note",
#             privacy_level=PrivacyLevel.PRIVATE,
#             tags=["old"],
#         )
#
# NEW:
#         note = Note(
#             text="Note",
#             entity_type=EntityType.PROJECT,
#             entity_id=1,
#             privacy_level=PrivacyLevel.PRIVATE,
#             tags=["old"],
#         )
