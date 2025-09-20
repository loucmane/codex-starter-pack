#!/usr/bin/env python3
"""Fix broken references in template files"""

import json
from pathlib import Path
import sys

def fix_references():
    fixes = [
        {
            "file": "templates/behaviors/file-operations/before-create.md",
            "old": "before-edit.md",
            "new": "templates/behaviors/file-operations/before-edit.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/behaviors/file-operations/before-edit.md",
            "old": "before-create.md",
            "new": "templates/behaviors/file-operations/before-create.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/behaviors/git/before-commit.md",
            "old": "../../templates/TOOLS.md",
            "new": "templates/TOOLS.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/behaviors/index.md",
            "old": "file-operations/before-edit.md",
            "new": "templates/behaviors/file-operations/before-edit.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/behaviors/index.md",
            "old": "file-operations/before-create.md",
            "new": "templates/behaviors/file-operations/before-create.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/behaviors/index.md",
            "old": "timestamps/before-adding.md",
            "new": "templates/behaviors/timestamps/before-adding.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/behaviors/index.md",
            "old": "git/before-commit.md",
            "new": "templates/behaviors/git/before-commit.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/behaviors/index.md",
            "old": "work-tracking/update-tracker.md",
            "new": "templates/behaviors/work-tracking/update-tracker.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/behaviors/index.md",
            "old": "validation/evidence-claims.md",
            "new": "templates/behaviors/validation/evidence-claims.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/behaviors/index.md",
            "old": "task-management/todo-write.md",
            "new": "templates/behaviors/task-management/todo-write.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/behaviors/index.md",
            "old": "session/session-end.md",
            "new": "templates/behaviors/session/session-end.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/behaviors/index.md",
            "old": "session/compaction-preparation.md",
            "new": "templates/behaviors/session/compaction-preparation.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/behaviors/index.md",
            "old": "session/compaction-detection.md",
            "new": "templates/behaviors/session/compaction-detection.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/behaviors/index.md",
            "old": "../templates/shared/patterns/ultrathink-format.md",
            "new": "templates/shared/patterns/ultrathink-format.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/behaviors/session/compaction-detection.md",
            "old": "compaction-preparation.md",
            "new": "templates/behaviors/session/compaction-preparation.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/behaviors/session/compaction-detection.md",
            "old": "session-end.md",
            "new": "templates/behaviors/session/session-end.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/behaviors/session/session-end.md",
            "old": "compaction-preparation.md",
            "new": "templates/behaviors/session/compaction-preparation.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/behaviors/validation/evidence-claims.md",
            "old": "../../templates/TOOLS.md",
            "new": "templates/TOOLS.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/guides/index.md",
            "old": "quickstart/getting-started.md",
            "new": "templates/guides/quickstart/getting-started.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/guides/index.md",
            "old": "ultrathink/understanding.md",
            "new": "templates/guides/ultrathink/understanding.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/guides/index.md",
            "old": "workflows/common.md",
            "new": "templates/guides/workflows/common.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/guides/index.md",
            "old": "workflows/patterns.md",
            "new": "templates/PATTERNS.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/guides/index.md",
            "old": "reference/triggers.md",
            "new": "templates/guides/reference/triggers.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/guides/index.md",
            "old": "reference/patterns.md",
            "new": "templates/PATTERNS.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/guides/index.md",
            "old": "troubleshooting/issues.md",
            "new": "templates/guides/troubleshooting/issues.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/guides/index.md",
            "old": "advanced/creating-handlers.md",
            "new": "templates/integration/guides/creating-handlers.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/guides/index.md",
            "old": "..templates/REGISTRY.md",
            "new": "templates/REGISTRY.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/handlers/tools/external/consult-gpt5.md",
            "old": "../debugging/debug-issue.md",
            "new": "templates/handlers/triggers/debug/debug-issue.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/integration/architecture/handler-architecture.md",
            "old": "system-architecture.md",
            "new": "templates/integration/architecture/system-architecture.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/integration/architecture/handler-architecture.md",
            "old": "template-architecture.md",
            "new": "templates/integration/architecture/template-architecture.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/integration/architecture/system-architecture.md",
            "old": "handler-architecture.md",
            "new": "templates/integration/architecture/handler-architecture.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/integration/architecture/system-architecture.md",
            "old": "template-architecture.md",
            "new": "templates/integration/architecture/template-architecture.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/integration/architecture/template-architecture.md",
            "old": "system-architecture.md",
            "new": "templates/integration/architecture/system-architecture.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/integration/architecture/template-architecture.md",
            "old": "handler-architecture.md",
            "new": "templates/integration/architecture/handler-architecture.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/integration/best-practices/handler-design.md",
            "old": "template-design.md",
            "new": "templates/integration/best-practices/template-design.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/integration/best-practices/handler-design.md",
            "old": "integration-patterns.md",
            "new": "templates/integration/best-practices/integration-patterns.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/integration/best-practices/integration-patterns.md",
            "old": "handler-design.md",
            "new": "templates/integration/best-practices/handler-design.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/integration/best-practices/integration-patterns.md",
            "old": "template-design.md",
            "new": "templates/integration/best-practices/template-design.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/integration/best-practices/template-design.md",
            "old": "handler-design.md",
            "new": "templates/integration/best-practices/handler-design.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/integration/best-practices/template-design.md",
            "old": "integration-patterns.md",
            "new": "templates/integration/best-practices/integration-patterns.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/integration/composition/handler-chaining.md",
            "old": "workflow-composition.md",
            "new": "templates/integration/composition/workflow-composition.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/integration/composition/handler-chaining.md",
            "old": "pattern-composition.md",
            "new": "templates/integration/composition/pattern-composition.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/integration/composition/pattern-composition.md",
            "old": "workflow-composition.md",
            "new": "templates/integration/composition/workflow-composition.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/integration/composition/pattern-composition.md",
            "old": "handler-chaining.md",
            "new": "templates/integration/composition/handler-chaining.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/integration/composition/workflow-composition.md",
            "old": "handler-chaining.md",
            "new": "templates/integration/composition/handler-chaining.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/integration/composition/workflow-composition.md",
            "old": "pattern-composition.md",
            "new": "templates/integration/composition/pattern-composition.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/integration/cross-system/mcp-integration.md",
            "old": "tool-integration.md",
            "new": "templates/integration/cross-system/tool-integration.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/integration/cross-system/mcp-integration.md",
            "old": "agent-coordination.md",
            "new": "templates/integration/cross-system/agent-coordination.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/integration/cross-system/tool-integration.md",
            "old": "mcp-integration.md",
            "new": "templates/integration/cross-system/mcp-integration.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/integration/guides/adding-agents.md",
            "old": "system-integration.md",
            "new": "templates/integration/guides/system-integration.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/integration/guides/adding-agents.md",
            "old": "creating-handlers.md",
            "new": "templates/integration/guides/creating-handlers.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/integration/guides/creating-handlers.md",
            "old": "system-integration.md",
            "new": "templates/integration/guides/system-integration.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/integration/guides/extending-templates.md",
            "old": "creating-handlers.md",
            "new": "templates/integration/guides/creating-handlers.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/integration/guides/system-integration.md",
            "old": "creating-handlers.md",
            "new": "templates/integration/guides/creating-handlers.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/integration/guides/system-integration.md",
            "old": "extending-templates.md",
            "new": "templates/integration/guides/extending-templates.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/integration/guides/system-integration.md",
            "old": "adding-agents.md",
            "new": "templates/integration/guides/adding-agents.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/matrices/index.md",
            "old": "routing/request-to-handler.md",
            "new": "templates/matrices/routing/request-to-handler.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/matrices/index.md",
            "old": "routing/context-to-mode.md",
            "new": "templates/matrices/routing/context-to-mode.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/matrices/index.md",
            "old": "selection/tool-selection.md",
            "new": "templates/patterns/selection/tool-selection.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/matrices/index.md",
            "old": "selection/file-to-convention.md",
            "new": "templates/matrices/selection/file-to-convention.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/matrices/index.md",
            "old": "recovery/error-to-recovery.md",
            "new": "templates/matrices/recovery/error-to-recovery.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/matrices/index.md",
            "old": "mapping/trigger-to-action.md",
            "new": "templates/matrices/mapping/trigger-to-action.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/matrices/index.md",
            "old": "mapping/keyword-to-handler.md",
            "new": "templates/matrices/mapping/keyword-to-handler.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/patterns/evidence/evidence-patterns.md",
            "old": "validation-patterns.md",
            "new": "templates/patterns/evidence/validation-patterns.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/patterns/evidence/evidence-patterns.md",
            "old": "proof-patterns.md",
            "new": "templates/patterns/evidence/proof-patterns.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/patterns/evidence/proof-patterns.md",
            "old": "evidence-patterns.md",
            "new": "templates/patterns/evidence/evidence-patterns.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/patterns/evidence/proof-patterns.md",
            "old": "validation-patterns.md",
            "new": "templates/patterns/evidence/validation-patterns.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/patterns/evidence/validation-patterns.md",
            "old": "evidence-patterns.md",
            "new": "templates/patterns/evidence/evidence-patterns.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/patterns/evidence/validation-patterns.md",
            "old": "proof-patterns.md",
            "new": "templates/patterns/evidence/proof-patterns.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/patterns/integration/composition.md",
            "old": "cross-system.md",
            "new": "templates/patterns/integration/cross-system.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/patterns/integration/cross-system.md",
            "old": "composition.md",
            "new": "templates/patterns/integration/composition.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/patterns/routing/intent-detection.md",
            "old": "request-analysis.md",
            "new": "templates/patterns/routing/request-analysis.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/patterns/routing/intent-detection.md",
            "old": "meta-routing.md",
            "new": "templates/patterns/routing/meta-routing.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/patterns/routing/meta-routing.md",
            "old": "request-analysis.md",
            "new": "templates/patterns/routing/request-analysis.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/patterns/routing/meta-routing.md",
            "old": "intent-detection.md",
            "new": "templates/patterns/routing/intent-detection.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/patterns/routing/request-analysis.md",
            "old": "meta-routing.md",
            "new": "templates/patterns/routing/meta-routing.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/patterns/routing/request-analysis.md",
            "old": "intent-detection.md",
            "new": "templates/patterns/routing/intent-detection.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/patterns/selection/agent-selection.md",
            "old": "handler-selection.md",
            "new": "templates/patterns/selection/handler-selection.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/patterns/selection/agent-selection.md",
            "old": "tool-selection.md",
            "new": "templates/patterns/selection/tool-selection.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/patterns/selection/handler-selection.md",
            "old": "tool-selection.md",
            "new": "templates/patterns/selection/tool-selection.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/patterns/selection/handler-selection.md",
            "old": "agent-selection.md",
            "new": "templates/patterns/selection/agent-selection.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/patterns/selection/tool-selection.md",
            "old": "handler-selection.md",
            "new": "templates/patterns/selection/handler-selection.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/patterns/selection/tool-selection.md",
            "old": "agent-selection.md",
            "new": "templates/patterns/selection/agent-selection.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/patterns/selection/tool-selection.md",
            "old": "../integration/code-creation.md",
            "new": "templates/handlers/orchestrators/code-creation.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/patterns/session/continuation-patterns.md",
            "old": "session-patterns.md",
            "new": "templates/patterns/session/session-patterns.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/patterns/session/continuation-patterns.md",
            "old": "state-patterns.md",
            "new": "templates/patterns/session/state-patterns.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/patterns/session/session-patterns.md",
            "old": "state-patterns.md",
            "new": "templates/patterns/session/state-patterns.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/patterns/session/session-patterns.md",
            "old": "continuation-patterns.md",
            "new": "templates/patterns/session/continuation-patterns.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/patterns/session/state-patterns.md",
            "old": "session-patterns.md",
            "new": "templates/patterns/session/session-patterns.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/patterns/session/state-patterns.md",
            "old": "continuation-patterns.md",
            "new": "templates/patterns/session/continuation-patterns.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/patterns/work-tracking/documentation-patterns.md",
            "old": "work-patterns.md",
            "new": "templates/patterns/work-tracking/work-patterns.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/patterns/work-tracking/documentation-patterns.md",
            "old": "progress-patterns.md",
            "new": "templates/patterns/work-tracking/progress-patterns.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/patterns/work-tracking/progress-patterns.md",
            "old": "work-patterns.md",
            "new": "templates/patterns/work-tracking/work-patterns.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/patterns/work-tracking/progress-patterns.md",
            "old": "documentation-patterns.md",
            "new": "templates/patterns/work-tracking/documentation-patterns.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/patterns/work-tracking/work-patterns.md",
            "old": "progress-patterns.md",
            "new": "templates/patterns/work-tracking/progress-patterns.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/patterns/work-tracking/work-patterns.md",
            "old": "documentation-patterns.md",
            "new": "templates/patterns/work-tracking/documentation-patterns.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/registry/index.md",
            "old": "../templates/USER-GUIDE.md",
            "new": "templates/USER-GUIDE.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/registry/index.md",
            "old": "handlers/triggers-registry.md",
            "new": "templates/registry/handlers/triggers-registry.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/registry/index.md",
            "old": "handlers/orchestrators-registry.md",
            "new": "templates/registry/handlers/orchestrators-registry.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/registry/index.md",
            "old": "handlers/operators-registry.md",
            "new": "templates/registry/handlers/operators-registry.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/registry/index.md",
            "old": "navigation/keywords.md",
            "new": "templates/registry/navigation/keywords.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/registry/index.md",
            "old": "behavioral/templates.md",
            "new": "templates/registry/behavioral/templates.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/registry/index.md",
            "old": "patterns/meta-routing.md",
            "new": "templates/patterns/routing/meta-routing.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/registry/index.md",
            "old": "behavioral/hooks.md",
            "new": "templates/registry/behavioral/hooks.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/registry/index.md",
            "old": "matrices/decision-matrices.md",
            "new": "templates/registry/matrices/decision-matrices.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/registry/index.md",
            "old": "conventions/special-files.md",
            "new": "templates/conventions/files/special-files.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/registry/index.md",
            "old": "../templates/handlers/orchestrators/resolve-session-void.md",
            "new": "templates/handlers/orchestrators/resolve-session-void.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/registry/index.md",
            "old": "../templates/handlers/operators/workflow/resolve-work-void.md",
            "new": "templates/handlers/operators/workflow/resolve-work-void.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/tools/index.md",
            "old": "search/serena-guide.md",
            "new": "templates/tools/search/serena-guide.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/tools/index.md",
            "old": "search/grep-patterns.md",
            "new": "templates/tools/search/grep-patterns.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/tools/index.md",
            "old": "file/edit-strategies.md",
            "new": "templates/tools/file/edit-strategies.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/tools/index.md",
            "old": "file/multi-edit.md",
            "new": "templates/tools/file/multi-edit.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/tools/index.md",
            "old": "git/commands.md",
            "new": "templates/tools/git/commands.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/tools/index.md",
            "old": "task/agent-usage.md",
            "new": "templates/tools/task/agent-usage.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/tools/index.md",
            "old": "../templates/REGISTRY.md",
            "new": "templates/REGISTRY.md",
            "action": "update_reference",
            "line_numbers": ""
        },
        {
            "file": "templates/tools/index.md",
            "old": "../templates/PROJECT-BLOG.md",
            "new": "templates/PROJECT-BLOG.md",
            "action": "update_reference",
            "line_numbers": ""
        },
    ]

    for fix in fixes:
        if fix['action'] == 'manual_review':
            print(f"⚠️  Manual review needed: {fix['file']} - {fix['old']}")
            continue

        file_path = Path(fix['file'])
        if not file_path.exists():
            print(f"❌ File not found: {fix['file']}")
            continue

        try:
            content = file_path.read_text()
            
            # Use scoped replacement if line numbers are available
            if fix.get('line_numbers') and fix['action'] == 'update_reference_scoped':
                lines = content.splitlines()
                line_nums = [int(n) for n in fix['line_numbers'].split(',') if n]
                changes_made = False
                
                # Replace only on specified lines (checking for markdown links and backticks)
                for line_num in line_nums:
                    if 1 <= line_num <= len(lines):
                        line_idx = line_num - 1
                        original_line = lines[line_idx]
                        import re
                        
                        # Pattern 1: Replace in markdown links [...](...)
                        pattern1 = r'\[([^\]]+)\]\(' + re.escape(fix['old']) + r'\)'
                        replacement1 = r'[\1](' + fix['new'] + ')'
                        updated_line = re.sub(pattern1, replacement1, original_line)
                        
                        # Pattern 2: Replace in backtick references `path`
                        if updated_line == original_line:  # If no markdown link was replaced
                            pattern2 = r'`' + re.escape(fix['old']) + r'`'
                            replacement2 = '`' + fix['new'] + '`'
                            updated_line = re.sub(pattern2, replacement2, original_line)
                        
                        if updated_line != original_line:
                            lines[line_idx] = updated_line
                            changes_made = True
                
                if changes_made:
                    updated = '\\n'.join(lines) + ('\\n' if content.endswith('\\n') else '')
                    file_path.write_text(updated)
                    print(f"✅ Fixed (scoped): {fix['file']} on lines {fix['line_numbers']}")
                else:
                    print(f"⚪ No change needed: {fix['file']}")
            else:
                # Fall back to global replacement
                updated = content.replace(fix['old'], fix['new'])
                if content != updated:
                    file_path.write_text(updated)
                    print(f"✅ Fixed (global): {fix['file']}")
                else:
                    print(f"⚪ No change needed: {fix['file']}")
        except Exception as e:
            print(f"❌ Error fixing {fix['file']}: {e}")

if __name__ == "__main__":
    print("Fixing broken references...")
    fix_references()
    print("Done!")
