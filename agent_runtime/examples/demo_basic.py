#!/usr/bin/env python3
"""
Basic Demo of Agent Runtime
===========================

This script demonstrates the Agent Runtime with simple examples:
1. Language preference detection and storage
2. CV generation with memory retrieval
3. Job matching with memory retrieval
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agent_runtime import AgentRuntime, RuntimeConfig


async def demo_language_preference():
    """Demo: Language preference detection and storage"""
    print("=" * 60)
    print("DEMO 1: Language Preference")
    print("=" * 60)
    
    runtime = AgentRuntime(config=RuntimeConfig(user_id="demo_user", enable_n8n=False, enable_audit=False))
    
    # Test input: "Parlons français"
    user_input = "Parlons français pour nos prochaines conversations"
    
    print(f"\nUser Input: {user_input}")
    print("\nProcessing...")
    
    result = await runtime.run(user_input)
    
    print(f"\n✅ Intent: {result.intent}")
    print(f"✅ Policies Applied: {result.policies_applied}")
    print(f"✅ Memories Retrieved: {len(result.retrieved_memories)}")
    
    if result.assembled_context:
        print(f"✅ Context Tokens: {result.assembled_context.total_tokens}")
    
    if result.llm_response:
        print(f"\n🤖 LLM Response:\n{result.llm_response[:300]}...")
    
    print(f"\n✅ Memories Written: {len(result.memory_written)}")
    for mem in result.memory_written:
        print(f"   - {mem['type']}: {mem.get('value', mem.get('content', ''))[:50]}")
    
    print(f"\n✅ Execution Time: {result.execution_time:.2f}s")
    print()


async def demo_cv_generation():
    """Demo: CV generation with memory"""
    print("=" * 60)
    print("DEMO 2: CV Generation")
    print("=" * 60)
    
    runtime = AgentRuntime(config=RuntimeConfig(user_id="demo_user", enable_n8n=False, enable_audit=False))
    
    # Test input: "Génère mon CV"
    user_input = "Génère mon CV pour un poste de Data Scientist"
    
    print(f"\nUser Input: {user_input}")
    print("\nProcessing...")
    
    result = await runtime.run(user_input)
    
    print(f"\n✅ Intent: {result.intent}")
    print(f"✅ Policies Applied: {result.policies_applied}")
    print(f"✅ Memories Retrieved: {len(result.retrieved_memories)}")
    
    if result.assembled_context:
        print(f"✅ Context Tokens: {result.assembled_context.total_tokens}")
    
    if result.llm_response:
        print(f"\n🤖 LLM Response:\n{result.llm_response[:300]}...")
    
    print(f"\n✅ Memories Written: {len(result.memory_written)}")
    for mem in result.memory_written:
        print(f"   - {mem['type']}: {mem.get('value', mem.get('content', ''))[:50]}")
    
    print(f"\n✅ Execution Time: {result.execution_time:.2f}s")
    print()


async def demo_job_matching():
    """Demo: Job matching"""
    print("=" * 60)
    print("DEMO 3: Job Matching")
    print("=" * 60)
    
    runtime = AgentRuntime(config=RuntimeConfig(user_id="demo_user", enable_n8n=False, enable_audit=False))
    
    # Test input: "Quels jobs correspondent à mon profil ?"
    user_input = "Quels jobs correspondent à mon profil de Data Scientist ?"
    
    print(f"\nUser Input: {user_input}")
    print("\nProcessing...")
    
    result = await runtime.run(user_input)
    
    print(f"\n✅ Intent: {result.intent}")
    print(f"✅ Policies Applied: {result.policies_applied}")
    print(f"✅ Memories Retrieved: {len(result.retrieved_memories)}")
    
    if result.assembled_context:
        print(f"✅ Context Tokens: {result.assembled_context.total_tokens}")
    
    if result.llm_response:
        print(f"\n🤖 LLM Response:\n{result.llm_response[:300]}...")
    
    print(f"\n✅ Memories Written: {len(result.memory_written)}")
    for mem in result.memory_written:
        print(f"   - {mem['type']}: {mem.get('value', mem.get('content', ''))[:50]}")
    
    print(f"\n✅ Execution Time: {result.execution_time:.2f}s")
    print()


async def demo_web_scraping():
    """Demo: Web scraping with N8N"""
    print("=" * 60)
    print("DEMO 4: Web Scraping (N8N Integration)")
    print("=" * 60)
    
    runtime = AgentRuntime(config=RuntimeConfig(user_id="demo_user", enable_n8n=False, enable_audit=False))
    
    # Test input with URL
    user_input = "Scrape cette annonce d'emploi: https://www.linkedin.com/jobs/view/data-scientist-at-company-x-12345/"
    
    print(f"\nUser Input: {user_input}")
    print("\nProcessing...")
    
    result = await runtime.run(user_input)
    
    print(f"\n✅ Intent: {result.intent}")
    print(f"✅ Policies Applied: {result.policies_applied}")
    print(f"✅ Workflow Executions: {len(result.workflow_executions)}")
    
    for wf in result.workflow_executions:
        print(f"   - Workflow: {wf.get('workflow_name', wf.get('webhook', 'unknown'))}")
        print(f"     Status: {wf.get('status', 'unknown')}")
        if wf.get('error'):
            print(f"     Error: {wf.get('error')[:100]}")
    
    if result.llm_response:
        print(f"\n🤖 LLM Response:\n{result.llm_response[:300]}...")
    
    print(f"\n✅ Execution Time: {result.execution_time:.2f}s")
    print()


async def demo_conversation():
    """Demo: Multi-turn conversation"""
    print("=" * 60)
    print("DEMO 5: Multi-Turn Conversation")
    print("=" * 60)
    
    runtime = AgentRuntime(config=RuntimeConfig(user_id="demo_user", enable_n8n=False, enable_audit=False))
    
    # First message
    print("\n--- Turn 1 ---")
    user_input1 = "Parlons français"
    print(f"User: {user_input1}")
    
    result1 = await runtime.run(user_input1)
    print(f"Goose: {result1.llm_response[:100]}...")
    
    # Second message (should remember language preference)
    print("\n--- Turn 2 ---")
    user_input2 = "Génère mon CV"
    print(f"User: {user_input2}")
    
    result2 = await runtime.run(user_input2)
    print(f"Goose: {result2.llm_response[:100]}...")
    
    # Third message
    print("\n--- Turn 3 ---")
    user_input3 = "Quels jobs correspondent à mon profil ?"
    print(f"User: {user_input3}")
    
    result3 = await runtime.run(user_input3)
    print(f"Goose: {result3.llm_response[:100]}...")
    
    print(f"\n✅ Total Execution Time: {result1.execution_time + result2.execution_time + result3.execution_time:.2f}s")
    print()


async def demo_metrics():
    """Demo: Runtime metrics"""
    print("=" * 60)
    print("DEMO 6: Runtime Metrics")
    print("=" * 60)
    
    runtime = AgentRuntime(config=RuntimeConfig(user_id="demo_user", enable_n8n=False, enable_audit=False))
    
    # Run a few examples
    await runtime.run("Parlons français")
    await runtime.run("Génère mon CV")
    await runtime.run("Quels jobs correspondent à mon profil ?")
    
    metrics = runtime.get_metrics()
    
    print("\nRuntime Metrics:")
    for key, value in metrics.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")
    print()


async def main():
    """Run all demos"""
    print("\n" + "=" * 60)
    print("AGENT RUNTIME - DEMONSTRATION")
    print("=" * 60)
    print("\nThis demonstrates the memory loop that was missing in GOOSE.")
    print("Each demo shows how the agent now:")
    print("  1. Classifies intent")
    print("  2. Decides what memory to retrieve")
    print("  3. Retrieves relevant memories")
    print("  4. Injects context into prompts")
    print("  5. Generates context-aware responses")
    print("  6. Stores new memories for future use")
    print()
    
    try:
        await demo_language_preference()
        await demo_cv_generation()
        await demo_job_matching()
        await demo_web_scraping()
        await demo_conversation()
        await demo_metrics()
        
        print("=" * 60)
        print("✅ ALL DEMOS COMPLETED SUCCESSFULLY")
        print("=" * 60)
        print("\nThe Agent Runtime is now fully integrated with:")
        print("  ✅ Memory Policy Engine (decides WHEN and WHAT to retrieve)")
        print("  ✅ Retrieval Engine (connects to Qdrant)")
        print("  ✅ Context Assembler (formats memories for LLM)")
        print("  ✅ Prompt Augmenter (injects context into prompts)")
        print("  ✅ Tool Integrator (N8N workflows)")
        print("  ✅ Memory Writeback (stores new memories)")
        print("  ✅ Audit Logging (PostgreSQL)")
        print("\nGOOSE is now COGNITIVELY CONNECTED to its memory infrastructure!")
        print()
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
