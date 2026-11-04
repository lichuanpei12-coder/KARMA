import json


def context_from_prompt(prompt):
    return json.loads(prompt.split('<feedback_input_json>')[1].split('</feedback_input_json>')[0])


def no_changes(context):
    result = {context['stage']: [], 'handoff': []}
    return result


def no_changes_call(prompt, **kwargs):
    return json.dumps(no_changes(context_from_prompt(prompt))), 0, 0, 0


def issue(issue_id, indices, source, finding='correct expression', sentence_id='S1'):
    return dict(issue_id=issue_id, sentence_ids=[sentence_id], related_indices=indices,
                evidence=source, finding=finding, result='apply correction')
