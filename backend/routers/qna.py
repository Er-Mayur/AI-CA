from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import User, TaxComputation, Conversation, Message
from schemas import QuestionRequest, QuestionResponse, ConversationResponse, ConversationCreate, MessageResponse
from dependencies import get_current_user
from utils.ollama_client import get_tax_advice, call_ollama
from utils.rag_engine import RAGEngine
from typing import List
from datetime import datetime

router = APIRouter()
rag = RAGEngine()

@router.post("/conversations", response_model=ConversationResponse)
def create_conversation(
    conversation_data: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new conversation"""
    conversation = Conversation(
        user_id=current_user.id,
        title=conversation_data.title or "New Chat"
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation

@router.get("/conversations", response_model=List[ConversationResponse])
def list_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all conversations for the current user"""
    conversations = db.query(Conversation).filter(
        Conversation.user_id == current_user.id
    ).order_by(Conversation.updated_at.desc()).all()
    return conversations

@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific conversation with all messages"""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    return conversation

@router.delete("/conversations/{conversation_id}")
def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a conversation"""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    db.delete(conversation)
    db.commit()
    return {"message": "Conversation deleted"}

@router.post("/ask", response_model=QuestionResponse)
async def ask_question(
    question_data: QuestionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Ask a tax-related question and get AI-powered answer"""
    
    # Create or get conversation
    if question_data.conversation_id:
        conversation = db.query(Conversation).filter(
            Conversation.id == question_data.conversation_id,
            Conversation.user_id == current_user.id
        ).first()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
    else:
        # Create new conversation with first question as title
        title = question_data.question[:50] + "..." if len(question_data.question) > 50 else question_data.question
        conversation = Conversation(
            user_id=current_user.id,
            title=title
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
    
    # Save user message
    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=question_data.question
    )
    db.add(user_message)
    
    # RAG: Retrieve context
    # Use provided financial year or default to current context if available
    target_year = question_data.financial_year
    
    context_text = ""
    try:
        # 1. Retrieve Context from RAG (Rules + User Documents)
        context_text = rag.search_context(
            query=question_data.question, 
            user_id=current_user.id,
            financial_year=target_year
        )
    except Exception as e:
        print(f"RAG Error: {e}")
        # Continue without context if RAG fails
    
    # 2. Add Computation Context if available (Legacy context method)
    computation_context = ""
    if target_year:
        computation = db.query(TaxComputation).filter(
            TaxComputation.user_id == current_user.id,
            TaxComputation.financial_year == target_year
        ).first()
        
        if computation:
            computation_context = f"""
COMPUTATION SUMMARY:
Total Income: {computation.gross_total_income}
Recommended Regime: {computation.recommended_regime}
Tax Payable: {computation.old_regime_total_tax if computation.recommended_regime == "Old Regime" else computation.new_regime_total_tax}
"""

    # 3. Construct Augmented Prompt
    system_prompt = "You are an expert Indian Tax AI. Answer based strictly on the provided context if available. Be concise."
    
    final_prompt = f"""
User Question: {question_data.question}

Context Information:
{context_text}
{computation_context}

Answer the user's question based on the above context. If the answer is not in the context, use general tax knowledge but mention that you are using general knowledge.
"""
    
    # Get AI answer
    try:
        # answer = await get_tax_advice(question_data.question, context) # Legacy call
        answer = await call_ollama(final_prompt, system_prompt)
        
        # Save assistant message
        assistant_message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=answer
        )
        db.add(assistant_message)
        
        # Update conversation timestamp
        conversation.updated_at = datetime.utcnow()
        
        db.commit()
        
        return QuestionResponse(
            question=question_data.question,
            answer=answer,
            conversation_id=conversation.id,
            sources=["Indian Income Tax Act", "Income Tax Department Guidelines"]
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting answer: {str(e)}"
        )

@router.get("/common-questions")
def get_common_questions():
    """Get list of common tax questions"""
    
    return {
        "questions": [
            {
                "category": "Tax Regimes",
                "questions": [
                    "What is the difference between old and new tax regime?",
                    "Which tax regime is better for me?",
                    "Can I switch between tax regimes?",
                    "What deductions are allowed in new regime?"
                ]
            },
            {
                "category": "Deductions",
                "questions": [
                    "What is Section 80C and how much can I save?",
                    "Can I claim HRA exemption?",
                    "What is the limit for health insurance deduction under 80D?",
                    "How does home loan interest deduction work?"
                ]
            },
            {
                "category": "ITR Filing",
                "questions": [
                    "Which ITR form should I use?",
                    "What is the deadline for ITR filing?",
                    "What happens if I miss the ITR deadline?",
                    "How do I claim tax refund?"
                ]
            },
            {
                "category": "Investments",
                "questions": [
                    "What are the best tax-saving investments?",
                    "Should I invest in NPS or PPF?",
                    "Can I get tax benefits on home loan?",
                    "What is ELSS and how does it save tax?"
                ]
            }
        ]
    }

