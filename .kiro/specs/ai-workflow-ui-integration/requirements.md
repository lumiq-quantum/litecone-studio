# Requirements Document

## Introduction

This document specifies the requirements for integrating AI-powered workflow generation capabilities into the existing workflow creation UI. The system will add a collapsible sidebar panel that enables users to generate workflow JSON through natural language descriptions or PDF document uploads, and iteratively refine workflows through an interactive chat interface. The generated workflows will automatically populate the existing JSON editor and visual graph components.

## Glossary

- **AI Generate Sidebar**: A collapsible right-side panel that contains AI workflow generation and chat functionality
- **Chat Session**: A stateful conversation between the user and the AI system for workflow generation and refinement
- **Workflow JSON Editor**: The existing Monaco-based JSON editor component where workflow definitions are written
- **Visual Graph**: The existing workflow visualization component that displays workflow steps and connections
- **Session State**: The conversation history and current workflow state maintained during the workflow creation process
- **AI Workflow API**: The backend REST API endpoints for AI-powered workflow generation at `/api/v1/ai-workflows`

## Requirements

### Requirement 1

**User Story:** As a user, I want to access AI workflow generation from the workflow creation page, so that I can choose between manual JSON editing and AI-assisted creation.

#### Acceptance Criteria

1. WHEN a user views the workflow creation page THEN the System SHALL display an "AI Generate" button next to the "Use Template" button in the header
2. WHEN a user clicks the "AI Generate" button THEN the System SHALL open a right sidebar panel overlaying the visual graph area
3. WHEN the sidebar is open THEN the System SHALL display a collapse/close button to hide the sidebar
4. WHEN a user closes the sidebar THEN the System SHALL preserve the JSON editor and visual graph state
5. WHEN a user reopens the sidebar THEN the System SHALL restore the previous chat session and conversation history

### Requirement 2

**User Story:** As a user, I want to generate workflows from text descriptions, so that I can create workflows without writing JSON manually.

#### Acceptance Criteria

1. WHEN the sidebar first opens THEN the System SHALL display a welcome message, text input field, and generate button
2. WHEN a user enters a workflow description THEN the System SHALL validate the description contains at least 3 words and is between 10-10,000 characters
3. WHEN a user clicks generate with a valid description THEN the System SHALL create a chat session and send the description to the AI Workflow API
4. WHEN the AI returns a workflow THEN the System SHALL populate the workflow JSON into the JSON editor
5. WHEN the workflow JSON is populated THEN the System SHALL trigger the visual graph to update automatically

### Requirement 3

**User Story:** As a user, I want to upload PDF documents to generate workflows, so that I can use existing requirement documents without retyping content.

#### Acceptance Criteria

1. WHEN the sidebar first opens THEN the System SHALL display a PDF upload button alongside the text input
2. WHEN a user clicks the upload button THEN the System SHALL open a file picker restricted to PDF files
3. WHEN a user selects a PDF file THEN the System SHALL validate the file size is under 10MB
4. WHEN a valid PDF is uploaded THEN the System SHALL send the file to the AI Workflow API upload endpoint
5. WHEN the AI returns a workflow from the PDF THEN the System SHALL populate the workflow JSON into the JSON editor and switch to chat interface

### Requirement 4

**User Story:** As a user, I want to refine workflows through chat, so that I can iteratively improve the generated workflow until it meets my requirements.

#### Acceptance Criteria

1. WHEN a workflow is generated THEN the System SHALL switch the sidebar to display a chat interface
2. WHEN the chat interface is displayed THEN the System SHALL show the conversation history with user messages and AI responses
3. WHEN a user sends a chat message THEN the System SHALL send the message to the AI Workflow API with the current session ID
4. WHEN the AI responds with an updated workflow THEN the System SHALL update the JSON editor with the new workflow JSON
5. WHEN the workflow is updated THEN the System SHALL display the AI's explanation of changes in the chat

### Requirement 5

**User Story:** As a user, I want to see loading states during AI generation, so that I understand the system is processing my request.

#### Acceptance Criteria

1. WHEN a user submits a generation request THEN the System SHALL display a loading indicator in the sidebar
2. WHEN a user sends a chat message THEN the System SHALL disable the input field and show a typing indicator
3. WHEN the AI is processing THEN the System SHALL display a loading skeleton in the chat area
4. WHEN the AI response is received THEN the System SHALL remove all loading indicators and enable the input field
5. WHEN generation takes longer than 5 seconds THEN the System SHALL display a progress message indicating the AI is working

### Requirement 6

**User Story:** As a user, I want to see errors clearly when generation fails, so that I can understand what went wrong and how to fix it.

#### Acceptance Criteria

1. WHEN the AI Workflow API returns an error THEN the System SHALL display the error message in the chat as a system message
2. WHEN validation errors occur THEN the System SHALL display the validation error details and suggestions in the chat
3. WHEN a rate limit is exceeded THEN the System SHALL display the retry-after time and disable input temporarily
4. WHEN a session expires THEN the System SHALL notify the user and offer to create a new session
5. WHEN network errors occur THEN the System SHALL display a retry button in the chat

### Requirement 7

**User Story:** As a user, I want the sidebar to preserve my chat history, so that I can review previous interactions and workflow iterations.

#### Acceptance Criteria

1. WHEN a user generates a workflow THEN the System SHALL store the chat session ID in component state
2. WHEN a user closes and reopens the sidebar THEN the System SHALL restore the chat history from the stored session
3. WHEN a user navigates away from the page THEN the System SHALL clear the session state
4. WHEN a user returns to the workflow creation page THEN the System SHALL start with a fresh session
5. WHEN the session expires on the backend THEN the System SHALL detect the expiration and create a new session on the next interaction

### Requirement 8

**User Story:** As a user, I want to manually edit AI-generated workflows, so that I can make fine-tuned adjustments without using chat.

#### Acceptance Criteria

1. WHEN a workflow is generated THEN the System SHALL allow the user to manually edit the JSON in the editor
2. WHEN a user manually edits the JSON THEN the System SHALL update the visual graph in real-time
3. WHEN a user sends a chat message after manual edits THEN the System SHALL send the manually edited workflow JSON to the AI
4. WHEN the AI responds THEN the System SHALL work with the manually edited version as the base
5. WHEN manual edits create invalid JSON THEN the System SHALL display validation errors in the JSON editor

### Requirement 9

**User Story:** As a user, I want to save AI-generated workflows, so that I can use them for workflow execution.

#### Acceptance Criteria

1. WHEN a user has a generated workflow THEN the System SHALL allow the user to use the existing "Create Workflow" button
2. WHEN a user clicks "Create Workflow" THEN the System SHALL validate and save the workflow using the existing workflow API
3. WHEN the workflow is saved successfully THEN the System SHALL navigate to the workflow detail page
4. WHEN the save fails THEN the System SHALL display the error in a toast notification
5. WHEN a user saves a workflow THEN the System SHALL keep the chat session active in case the user returns

### Requirement 10

**User Story:** As a user, I want clear visual feedback about workflow changes, so that I can verify the AI made the correct modifications.

#### Acceptance Criteria

1. WHEN the AI updates a workflow THEN the System SHALL highlight the changed lines in the JSON editor
2. WHEN the visual graph updates THEN the System SHALL animate the changes to draw attention
3. WHEN the AI explains changes THEN the System SHALL display the explanation prominently in the chat
4. WHEN multiple changes are made THEN the System SHALL provide a summary of all modifications
5. WHEN the workflow structure changes significantly THEN the System SHALL provide a before/after comparison option

### Requirement 11

**User Story:** As a user, I want the sidebar to be responsive, so that I can use AI generation on different screen sizes.

#### Acceptance Criteria

1. WHEN the viewport width is less than 1024px THEN the System SHALL make the sidebar full-width and overlay the entire content
2. WHEN the viewport width is 1024px or greater THEN the System SHALL display the sidebar as a right panel with fixed width
3. WHEN the sidebar is open on mobile THEN the System SHALL hide the JSON editor and visual graph
4. WHEN the sidebar is closed on mobile THEN the System SHALL restore the JSON editor and visual graph
5. WHEN the user rotates the device THEN the System SHALL adjust the sidebar layout appropriately

### Requirement 12

**User Story:** As a user, I want helpful initial guidance, so that I understand how to use the AI generation feature.

#### Acceptance Criteria

1. WHEN the sidebar first opens THEN the System SHALL display a welcome message explaining the feature
2. WHEN the welcome message is displayed THEN the System SHALL include examples of good workflow descriptions
3. WHEN the user has not generated a workflow THEN the System SHALL show placeholder text in the input field with an example
4. WHEN the user hovers over the PDF upload button THEN the System SHALL display a tooltip explaining supported formats and size limits
5. WHEN the user starts typing THEN the System SHALL display character count and validation feedback

