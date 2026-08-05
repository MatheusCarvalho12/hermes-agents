## Description: <br>
Evaluates test suites for coverage gaps, TDD/BDD compliance, and anti-patterns. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[athola](https://clawhub.ai/user/athola) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
Developers and engineers use this skill to audit test suites before releases or after failures, identifying framework coverage, scenario quality issues, invariant erosion, and concrete remediation actions. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: Suggested local commands may inspect repository files, run tests, generate coverage artifacts, or install test tooling. <br>
Mitigation: Review each command for the target repository before execution, and approve package installation or coverage tooling explicitly. <br>
Risk: Broad test-audit triggers can produce recommendations without enough project-specific evidence. <br>
Mitigation: Require the agent to log executed commands, outputs, coverage data, and cited evidence before accepting quality or release recommendations. <br>


## Reference(s): <br>
- [ClawHub skill page](https://clawhub.ai/athola/skills/nm-pensive-test-review) <br>
- [Project homepage from ClawHub metadata](https://github.com/athola/claude-night-market/tree/master/plugins/pensive) <br>
- [Publisher profile](https://clawhub.ai/user/athola) <br>


## Skill Output: <br>
**Output Type(s):** [Analysis, Markdown, Shell commands, Guidance] <br>
**Output Format:** [Markdown with structured review sections and inline shell commands] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [May include framework detection, coverage findings, quality issues, remediation plans, and approval recommendations.] <br>

## Skill Version(s): <br>
1.9.17 (source: server release metadata) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
