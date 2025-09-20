# Subagent System Capability Assessment

## Your Task

You are being asked to perform a comprehensive evaluation of the template system in this codebase. Your goal is to understand how the AI assistant is supposed to operate and verify that all documented behaviors are functioning correctly.

## Evaluation Scope

Please conduct a thorough analysis covering:

1. **System Discovery**
   - Identify the primary configuration and control mechanisms for the AI
   - Document the execution flow and decision-making process
   - Map out how requests are processed from start to finish

2. **Behavioral Analysis**
   - Determine what protocols or patterns the AI should follow
   - Identify any enforcement mechanisms or required behaviors
   - Document how the AI should handle different types of requests

3. **Template System Evaluation**
   - Analyze the template organization and structure
   - Verify that all referenced components are accessible
   - Test the loading and execution of various handlers

4. **Request Processing Tests**
   Execute and document the complete flow for these scenarios:
   
   a) **Bug Fix Request**: "I have a bug in my authentication code"
      - Document every step from request receipt to completion
      - Identify all templates, handlers, and protocols involved
      - Verify the execution follows documented patterns

   b) **Feature Implementation**: "Add a new dashboard to my app"
      - Trace the complete execution path
      - Document all decision points and handler selections
      - Verify compliance with any required formats or protocols

   c) **Code Analysis**: "Explain how this function works"
      - Map the analysis workflow
      - Document tool selection and usage
      - Verify output format compliance

   d) **Natural Conversation**: "How's the weather today?"
      - Document how non-technical requests are handled
      - Identify any special protocols for casual conversation
      - Verify appropriate response patterns

5. **Compliance Verification**
   - Check if there are any mandatory formats or structures that must be followed
   - Verify that all required checks and validations are performed
   - Document any enforcement mechanisms and their effectiveness

6. **Error Handling**
   - Test what happens when handlers are missing
   - Verify fallback mechanisms work correctly
   - Document recovery strategies for various failure modes

7. **Cross-Reference Validation**
   - Verify all module references resolve correctly
   - Check that import statements lead to valid files
   - Confirm handler discovery mechanisms work

8. **Performance Assessment**
   - Measure initialization and loading times
   - Assess the efficiency of the modular structure
   - Document any bottlenecks or inefficiencies

## Required Output

Provide a detailed report including:

1. **System Architecture Overview**
   - Primary control files and their roles
   - Execution flow diagram
   - Key decision points

2. **Test Results Matrix**
   - Each test scenario with pass/fail status
   - Detailed execution traces
   - Deviations from expected behavior

3. **Compliance Report**
   - List all mandatory protocols discovered
   - Verification of enforcement mechanisms
   - Gaps or violations found

4. **Critical Issues**
   - Any broken references or missing components
   - Violations of documented behaviors
   - System failures or errors

5. **Recommendations**
   - Improvements for system reliability
   - Missing components that should be added
   - Optimization opportunities

## Evaluation Criteria

Your analysis will be assessed on:
- Thoroughness of system discovery
- Accuracy in identifying control mechanisms
- Completeness of test execution
- Quality of documentation
- Identification of actual vs. documented behavior

## Important Notes

- Start from first principles - discover the system organically
- Document your discovery process step-by-step
- Test actual execution, not just documentation
- Verify claims with evidence from the codebase
- Be critical and thorough in your assessment

Begin by exploring the codebase to understand its structure, then systematically work through each evaluation area. Focus on what actually happens when requests are processed, not just what the documentation says should happen.