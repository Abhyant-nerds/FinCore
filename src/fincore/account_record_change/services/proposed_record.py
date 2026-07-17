"""Build proposed records deterministically from request changes."""

from ..models import FieldAction, OperationType, ProposedRecord, RecordSnapshot, ChangeRequest


class ProposedRecordService:
    def build(self, request: ChangeRequest, existing_record: RecordSnapshot | None) -> ProposedRecord:
        if request.operation == OperationType.ADD:
            fields = {}
            base_version = None
            record_id = request.record_id
        else:
            if not existing_record:
                raise ValueError("Existing record is required for UPDATE and DELETE")
            fields = dict(existing_record.fields)
            base_version = existing_record.version
            record_id = existing_record.record_id

        if request.operation == OperationType.DELETE:
            return ProposedRecord(
                record_id=record_id,
                entity_type=request.entity_type,
                account_type=request.account_type,
                base_version=base_version,
                fields=fields,
                changed_fields=[],
            )

        for change in request.changes:
            if change.action in {FieldAction.ADD, FieldAction.REPLACE}:
                fields[change.field_path] = change.new_value
            elif change.action == FieldAction.REMOVE:
                fields.pop(change.field_path, None)

        return ProposedRecord(
            record_id=record_id,
            entity_type=request.entity_type,
            account_type=request.account_type,
            base_version=base_version,
            fields=fields,
            changed_fields=[change.field_path for change in request.changes],
        )

