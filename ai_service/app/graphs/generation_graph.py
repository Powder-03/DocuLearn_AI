from typing import Dict, Any
from langgraph.graph import StateGraph, END
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain.schema import messages_to_dict, messages_from_dict

from app.graphs.state import GenerationGraphState
from app.core.llm_factory import get_llm
from app.services.memory import get_session_state, update_session_state


def plan_generator_node(state: GenerationGraphState) -> Dict[str, Any]:
    """
    Planning node that generates a JSON lesson plan.
    Runs only once per session to create the learning roadmap.
    """
    # Use Gemini for planning
    llm = get_llm("google", "gemini-2.0-flash-exp", temperature=0.7)
    
    # Create a prompt for generating the lesson plan
    planning_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert educational planner. Create a detailed, day-by-day lesson plan in JSON format.
        
The plan should be engaging, progressive, and tailored to the specified time commitment per day.
Break down the topic into logical subtopics and ensure each day builds on previous knowledge.

Return ONLY valid JSON in this exact format:
{{
  "topic": "Main Topic Name",
  "total_days": <number>,
  "days": [
    {{
      "day": 1,
      "title": "Day 1 Title",
      "subtopic": "Specific subtopic for this day",
      "learning_objectives": ["Objective 1", "Objective 2"],
      "key_concepts": ["Concept 1", "Concept 2"],
      "activities": ["Activity 1", "Activity 2"],
      "estimated_time": "30 minutes"
    }},
    ...
  ]
}}"""),
        ("human", """Create a {total_days}-day lesson plan for learning about: {topic}

Time available per day: {time_per_day}

Generate a comprehensive, structured learning plan.""")
    ])
    
    # Generate the lesson plan
    chain = planning_prompt | llm | JsonOutputParser()
    
    plan_json = chain.invoke({
        "topic": state["topic"],
        "total_days": state["total_days"],
        "time_per_day": state["time_per_day"]
    })
    
    # Create an AI message announcing the plan creation
    announcement = AIMessage(
        content=f"I've created a {state['total_days']}-day personalized learning plan for '{state['topic']}'! "
                f"Each day is designed for {state['time_per_day']} of focused learning. "
                f"Let's start with Day 1: {plan_json['days'][0]['title']}. Ready to begin?"
    )
    
    # Persist to database
    update_session_state(
        state["session_id"],
        {
            "lesson_plan": plan_json,
            "current_day": 1,
            "topic": state["topic"],
            "chat_history": [announcement]
        }
    )
    
    # Return updates to graph state
    return {
        "lesson_plan": plan_json,
        "current_day": 1,
        "chat_history": [announcement]
    }


def tutor_node(state: GenerationGraphState) -> Dict[str, Any]:
    """
    Tutoring node that handles all subsequent chat interactions.
    Follows the generated lesson plan and guides the learner.
    """
    # Use GPT-4o for tutoring
    llm = get_llm("openai", "gpt-4o", temperature=0.8)
    
    # Get the latest session state from database
    session_id = state["session_id"]
    db_state = get_session_state(session_id)
    
    lesson_plan = db_state["lesson_plan"]
    current_day = db_state["current_day"]
    memory_summary = db_state.get("memory_summary", "")
    
    # Get the current day's lesson
    if lesson_plan and "days" in lesson_plan:
        current_lesson = next(
            (day for day in lesson_plan["days"] if day["day"] == current_day),
            lesson_plan["days"][0]
        )
    else:
        current_lesson = {"title": "General Learning", "subtopic": state["topic"]}
    
    # Build the system prompt with context
    system_prompt = f"""You are an engaging, patient, and knowledgeable AI tutor following a structured lesson plan.

**Current Lesson Context:**
- Day {current_day} of {lesson_plan.get('total_days', 'N/A')}
- Topic: {current_lesson.get('title', 'Learning Session')}
- Subtopic: {current_lesson.get('subtopic', '')}
- Learning Objectives: {', '.join(current_lesson.get('learning_objectives', []))}
- Key Concepts: {', '.join(current_lesson.get('key_concepts', []))}

**Your Teaching Approach:**
1. Use the Socratic method - guide with questions rather than just providing answers
2. Check for understanding before moving forward
3. Provide examples and analogies to clarify concepts
4. Encourage active learning and critical thinking
5. Be encouraging and supportive
6. Adapt to the learner's pace and understanding level

**Previous Conversation Summary:**
{memory_summary if memory_summary else "This is the beginning of the conversation."}

Guide the learner through today's lesson, ensuring they grasp each concept before progressing."""
    
    # Build the message history for the LLM
    messages = [SystemMessage(content=system_prompt)] + state["chat_history"]
    
    # Get AI response
    ai_response = llm.invoke(messages)
    
    # Update chat history
    new_history = state["chat_history"] + [ai_response]
    
    # Persist updated chat history to database
    update_session_state(session_id, {"chat_history": new_history})
    
    # TODO: Add logic to update memory_summary periodically (e.g., every 5-10 messages)
    # This could involve calling another LLM to summarize the conversation
    
    # Return updates to graph state
    return {
        "chat_history": [ai_response]
    }


def should_plan(state: GenerationGraphState) -> str:
    """
    Conditional entry point to determine if planning is needed.
    
    Returns:
        "plan_generator" if no lesson plan exists
        "tutor" if lesson plan already exists
    """
    lesson_plan = state.get("lesson_plan")
    
    if not lesson_plan or not lesson_plan.get("days"):
        return "plan_generator"
    else:
        return "tutor"


# Build the LangGraph workflow
workflow = StateGraph(GenerationGraphState)

# Add nodes
workflow.add_node("plan_generator", plan_generator_node)
workflow.add_node("tutor", tutor_node)

# Set conditional entry point
workflow.set_conditional_entry_point(
    should_plan,
    {
        "plan_generator": "plan_generator",
        "tutor": "tutor"
    }
)

# Add edges
workflow.add_edge("plan_generator", "tutor")
workflow.add_edge("tutor", END)

# Compile the graph (no checkpointer - we handle persistence manually)
generation_app = workflow.compile()
