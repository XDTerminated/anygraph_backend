SELECT
    cs.chat_session_id,
    cs.email,
    cs.chat_session_title,
    cs.created_at,
    COUNT(d.dataset_url) as dataset_count
FROM chat_sessions cs
LEFT JOIN datasets d ON cs.chat_session_id = d.chat_session_id
WHERE cs.email = %s
GROUP BY cs.chat_session_id, cs.email, cs.chat_session_title, cs.created_at
ORDER BY cs.created_at DESC;
