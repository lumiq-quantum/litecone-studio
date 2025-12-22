# Practical Input Mapping Examples

Real-world examples showing how to access multiple data fields from agents like `fetch_data` with complex outputs.

## 📊 Example: fetch_data Step with Rich Output

Imagine your `fetch_data` step returns this complex structure:

```json
{
  "text": "Successfully extracted 150 pages of content from the PDF document.",
  "response": "PDF processing completed with high confidence.",
  "id": "task-abc123-def456",
  "task_id": "fetch-pdf-content-789",
  "kind": "task",
  "status": {
    "state": "completed",
    "timestamp": "2024-01-15T10:30:00Z",
    "processing_time_ms": 2500
  },
  "artifacts": [
    {
      "parts": [
        {
          "kind": "text",
          "text": "Extracted PDF content here..."
        }
      ],
      "artifactId": "pdf-content-artifact"
    }
  ],
  "metadata": {
    "adk_author": "pdf_extractor_agent",
    "file_info": {
      "filename": "document.pdf",
      "size_bytes": 2048000,
      "pages": 150,
      "format": "PDF/A-1b"
    },
    "extraction_stats": {
      "text_blocks": 450,
      "images": 23,
      "tables": 12,
      "confidence_score": 0.95
    },
    "adk_usage_metadata": {
      "totalTokenCount": 1250,
      "processing_model": "advanced-pdf-v2"
    }
  },
  "context_id": "session-xyz789",
  "extracted_data": {
    "title": "Annual Financial Report 2024",
    "author": "Finance Department",
    "creation_date": "2024-01-10",
    "sections": [
      {
        "title": "Executive Summary",
        "page_start": 1,
        "page_end": 5,
        "content": "Executive summary content..."
      },
      {
        "title": "Financial Analysis", 
        "page_start": 6,
        "page_end": 45,
        "content": "Financial analysis content..."
      }
    ],
    "tables": [
      {
        "title": "Revenue Summary",
        "page": 12,
        "data": [
          {"quarter": "Q1", "revenue": 1000000},
          {"quarter": "Q2", "revenue": 1200000}
        ]
      }
    ],
    "key_figures": {
      "total_revenue": 4500000,
      "net_profit": 650000,
      "growth_rate": 0.15
    }
  }
}
```

## 🎯 All Possible Input Mappings

### 1. Basic Field Access
```json
{
  "input_mapping": {
    "main_content": "${fetch_data.output.text}",
    "agent_message": "${fetch_data.output.response}",
    "task_reference": "${fetch_data.output.id}",
    "original_task": "${fetch_data.output.task_id}",
    "response_type": "${fetch_data.output.kind}"
  }
}
```

### 2. Status Information
```json
{
  "input_mapping": {
    "completion_status": "${fetch_data.output.status.state}",
    "completion_time": "${fetch_data.output.status.timestamp}",
    "processing_duration": "${fetch_data.output.status.processing_time_ms}",
    "full_status": "${fetch_data.output.status}"
  }
}
```

### 3. File Metadata Access
```json
{
  "input_mapping": {
    "filename": "${fetch_data.output.metadata.file_info.filename}",
    "file_size": "${fetch_data.output.metadata.file_info.size_bytes}",
    "page_count": "${fetch_data.output.metadata.file_info.pages}",
    "pdf_format": "${fetch_data.output.metadata.file_info.format}",
    "complete_file_info": "${fetch_data.output.metadata.file_info}"
  }
}
```

### 4. Extraction Statistics
```json
{
  "input_mapping": {
    "text_blocks_found": "${fetch_data.output.metadata.extraction_stats.text_blocks}",
    "images_found": "${fetch_data.output.metadata.extraction_stats.images}",
    "tables_found": "${fetch_data.output.metadata.extraction_stats.tables}",
    "confidence_level": "${fetch_data.output.metadata.extraction_stats.confidence_score}",
    "all_stats": "${fetch_data.output.metadata.extraction_stats}"
  }
}
```

### 5. Extracted Document Data
```json
{
  "input_mapping": {
    "document_title": "${fetch_data.output.extracted_data.title}",
    "document_author": "${fetch_data.output.extracted_data.author}",
    "creation_date": "${fetch_data.output.extracted_data.creation_date}",
    "all_sections": "${fetch_data.output.extracted_data.sections}",
    "financial_tables": "${fetch_data.output.extracted_data.tables}",
    "key_metrics": "${fetch_data.output.extracted_data.key_figures}"
  }
}
```

### 6. Specific Section Access
```json
{
  "input_mapping": {
    "executive_summary": "${fetch_data.output.extracted_data.sections[0].content}",
    "financial_analysis": "${fetch_data.output.extracted_data.sections[1].content}",
    "first_section_title": "${fetch_data.output.extracted_data.sections[0].title}",
    "first_section_pages": "${fetch_data.output.extracted_data.sections[0].page_start}"
  }
}
```

### 7. Financial Data Access
```json
{
  "input_mapping": {
    "total_revenue": "${fetch_data.output.extracted_data.key_figures.total_revenue}",
    "net_profit": "${fetch_data.output.extracted_data.key_figures.net_profit}",
    "growth_rate": "${fetch_data.output.extracted_data.key_figures.growth_rate}",
    "revenue_table": "${fetch_data.output.extracted_data.tables[0].data}",
    "q1_revenue": "${fetch_data.output.extracted_data.tables[0].data[0].revenue}"
  }
}
```

### 8. Agent Metadata
```json
{
  "input_mapping": {
    "processing_agent": "${fetch_data.output.metadata.adk_author}",
    "token_usage": "${fetch_data.output.metadata.adk_usage_metadata.totalTokenCount}",
    "processing_model": "${fetch_data.output.metadata.adk_usage_metadata.processing_model}",
    "session_context": "${fetch_data.output.context_id}"
  }
}
```

### 9. Artifacts Access
```json
{
  "input_mapping": {
    "artifact_content": "${fetch_data.output.artifacts[0].parts[0].text}",
    "artifact_id": "${fetch_data.output.artifacts[0].artifactId}",
    "all_artifacts": "${fetch_data.output.artifacts}"
  }
}
```

## 🔄 Multi-Step Processing Examples

### Example 1: PDF Analysis Workflow
```json
{
  "steps": {
    "fetch_data": {
      "id": "fetch_data",
      "agent_name": "pdf_extractor",
      "next_step": "analyze_content",
      "input_mapping": {
        "pdf_url": "${workflow.input.document_url}",
        "extraction_mode": "detailed"
      }
    },
    "analyze_content": {
      "id": "analyze_content", 
      "agent_name": "content_analyzer",
      "next_step": "generate_summary",
      "input_mapping": {
        "document_text": "${fetch_data.output.text}",
        "document_title": "${fetch_data.output.extracted_data.title}",
        "page_count": "${fetch_data.output.metadata.file_info.pages}",
        "confidence_score": "${fetch_data.output.metadata.extraction_stats.confidence_score}",
        "sections_to_analyze": "${fetch_data.output.extracted_data.sections}",
        "analysis_type": "${workflow.input.analysis_type}"
      }
    },
    "generate_summary": {
      "id": "generate_summary",
      "agent_name": "summarizer",
      "next_step": null,
      "input_mapping": {
        "original_content": "${fetch_data.output.text}",
        "analysis_results": "${analyze_content.output.text}",
        "document_metadata": {
          "title": "${fetch_data.output.extracted_data.title}",
          "author": "${fetch_data.output.extracted_data.author}",
          "pages": "${fetch_data.output.metadata.file_info.pages}",
          "confidence": "${fetch_data.output.metadata.extraction_stats.confidence_score}"
        },
        "key_figures": "${fetch_data.output.extracted_data.key_figures}",
        "summary_length": "${workflow.input.summary_length}"
      }
    }
  }
}
```

### Example 2: Financial Data Processing
```json
{
  "steps": {
    "fetch_data": {
      "id": "fetch_data",
      "agent_name": "financial_extractor",
      "next_step": "validate_data",
      "input_mapping": {
        "report_url": "${workflow.input.financial_report_url}"
      }
    },
    "validate_data": {
      "id": "validate_data",
      "agent_name": "data_validator", 
      "next_step": "calculate_metrics",
      "input_mapping": {
        "revenue_data": "${fetch_data.output.extracted_data.key_figures.total_revenue}",
        "profit_data": "${fetch_data.output.extracted_data.key_figures.net_profit}",
        "growth_rate": "${fetch_data.output.extracted_data.key_figures.growth_rate}",
        "quarterly_data": "${fetch_data.output.extracted_data.tables[0].data}",
        "validation_rules": "${workflow.input.validation_criteria}",
        "confidence_threshold": 0.9
      }
    },
    "calculate_metrics": {
      "id": "calculate_metrics",
      "agent_name": "metrics_calculator",
      "next_step": null,
      "input_mapping": {
        "validated_revenue": "${validate_data.output.validated_revenue}",
        "validated_profit": "${validate_data.output.validated_profit}",
        "original_growth_rate": "${fetch_data.output.extracted_data.key_figures.growth_rate}",
        "quarterly_breakdown": "${fetch_data.output.extracted_data.tables[0].data}",
        "calculation_type": "${workflow.input.metrics_to_calculate}",
        "benchmark_data": "${workflow.input.industry_benchmarks}"
      }
    }
  }
}
```

## 🎨 Advanced Patterns

### 1. Conditional Data Selection
```json
{
  "input_mapping": {
    "primary_content": "${fetch_data.output.text}",
    "fallback_content": "${fetch_data.output.artifacts[0].parts[0].text}",
    "use_high_confidence": "${fetch_data.output.metadata.extraction_stats.confidence_score}",
    "processing_mode": "${workflow.input.quality_mode}"
  }
}
```

### 2. Dynamic Message Construction
```json
{
  "input_mapping": {
    "status_message": "Processed ${fetch_data.output.metadata.file_info.filename} (${fetch_data.output.metadata.file_info.pages} pages) with ${fetch_data.output.metadata.extraction_stats.confidence_score} confidence",
    "processing_summary": "Extracted ${fetch_data.output.metadata.extraction_stats.text_blocks} text blocks, ${fetch_data.output.metadata.extraction_stats.images} images, and ${fetch_data.output.metadata.extraction_stats.tables} tables",
    "file_reference": "${workflow.input.output_path}/${fetch_data.output.extracted_data.title}_processed.json"
  }
}
```

### 3. Data Aggregation
```json
{
  "input_mapping": {
    "complete_document_info": {
      "source": {
        "filename": "${fetch_data.output.metadata.file_info.filename}",
        "size": "${fetch_data.output.metadata.file_info.size_bytes}",
        "pages": "${fetch_data.output.metadata.file_info.pages}"
      },
      "content": {
        "title": "${fetch_data.output.extracted_data.title}",
        "author": "${fetch_data.output.extracted_data.author}",
        "sections": "${fetch_data.output.extracted_data.sections}"
      },
      "processing": {
        "agent": "${fetch_data.output.metadata.adk_author}",
        "confidence": "${fetch_data.output.metadata.extraction_stats.confidence_score}",
        "duration": "${fetch_data.output.status.processing_time_ms}"
      }
    }
  }
}
```

## 🔍 Debugging Complex Mappings

### 1. Test Individual Fields First
```json
// Start with simple mappings
{
  "test_text": "${fetch_data.output.text}",
  "test_title": "${fetch_data.output.extracted_data.title}"
}

// Then add complexity
{
  "test_nested": "${fetch_data.output.metadata.file_info.pages}",
  "test_array": "${fetch_data.output.extracted_data.sections[0].title}"
}
```

### 2. Use Safe Fallbacks
```json
{
  "primary_data": "${fetch_data.output.extracted_data.title}",
  "fallback_data": "${fetch_data.output.text}",
  "safe_identifier": "${fetch_data.output.id}"
}
```

### 3. Validate Data Types
```json
{
  "string_field": "${fetch_data.output.text}",
  "number_field": "${fetch_data.output.metadata.file_info.pages}",
  "object_field": "${fetch_data.output.metadata.file_info}",
  "array_field": "${fetch_data.output.extracted_data.sections}"
}
```

## 📋 Summary

With a rich `fetch_data` output, you can access:

- ✅ **Basic fields**: `text`, `response`, `id`, `task_id`
- ✅ **Status info**: `status.state`, `status.timestamp`
- ✅ **File metadata**: `metadata.file_info.*`
- ✅ **Processing stats**: `metadata.extraction_stats.*`
- ✅ **Extracted content**: `extracted_data.*`
- ✅ **Nested structures**: `sections[0].title`, `tables[0].data`
- ✅ **Complex objects**: Complete metadata, sections, tables
- ✅ **Dynamic content**: String interpolation with multiple fields

The key is understanding your agent's output structure and using the correct path to access the data you need!