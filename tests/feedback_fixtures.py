import json


def context_from_prompt(prompt):
    return json.loads(prompt.split('<feedback_input_json>')[1].split('</feedback_input_json>')[0])


def no_changes(context):
    return dict(reviewed_sentence_ids=[s['sentence_id'] for s in context['source_sentences']],
                reviewed_indices=[t['index'] for t in context['current_collection']['triples']],
                issues=[], handoff=[], handoff_results=[dict(issue_id=h['id'], status='still_open', reason='retained for review')
                                                       for h in context['handoff']],
                add=[], replace=[], remove=[])


def no_changes_call(prompt, **kwargs):
    return json.dumps(no_changes(context_from_prompt(prompt))), 0, 0, 0


def issue(issue_id, indices, source, finding='correct expression', sentence_id='S1'):
    return dict(issue_id=issue_id, sentence_ids=[sentence_id], related_indices=indices,
                evidence=source, finding=finding, result='apply correction')
