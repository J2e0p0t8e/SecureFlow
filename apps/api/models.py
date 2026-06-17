"""
Modèles Django pour l'API SecureFlow AI.
Personne 2 - Backend & Ingestion.
"""

from django.db import models


class AnalysisSession(models.Model):
    """
    Représente une session d'analyse (Mode A, B ou C).
    Stocke les résultats et permet de retrouver la Band Room associée.
    """
    
    MODE_CHOICES = [
        ("A", "Mode A - Audit de sécurité"),
        ("B", "Mode B - Pipeline de développement"),
        ("C", "Mode C - Rapport PDF"),
    ]
    
    INPUT_TYPE_CHOICES = [
        ("github", "GitHub Repository"),
        ("zip", "ZIP Upload"),
        ("text", "Code collé"),
    ]
    
    # Identifiants
    mode = models.CharField(max_length=1, choices=MODE_CHOICES, db_index=True)
    room_id = models.CharField(max_length=64, unique=True, db_index=True, 
                               help_text="UUID de la Band Room")
    audit_id = models.CharField(max_length=50, blank=True, 
                               help_text="ID d'audit généré par les agents (ex: SF-AUDIT-20260614-1234)")
    
    # Entrée utilisateur
    input_type = models.CharField(max_length=20, choices=INPUT_TYPE_CHOICES)
    input_source = models.TextField(blank=True, 
                                    help_text="URL GitHub ou nom du fichier ZIP")
    project_label = models.CharField(max_length=200, blank=True,
                                    help_text="Nom du projet (optionnel)")
    
    # Résultats
    decision = models.CharField(max_length=20, blank=True,
                               help_text="Décision finale (Mode A: VALIDER/CORRIGER/CRITIQUE)")
    final_report = models.TextField(blank=True,
                                   help_text="Rapport final de l'agent décisionnel")
    result_json = models.JSONField(default=dict,
                                  help_text="Réponse JSON complète de l'orchestrateur")
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    duration_seconds = models.IntegerField(null=True, blank=True,
                                          help_text="Durée d'exécution en secondes")
    
    # Statut
    STATUS_CHOICES = [
        ("pending", "En attente"),
        ("running", "En cours"),
        ("completed", "Terminé"),
        ("failed", "Échoué"),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, 
                             default="pending", db_index=True)
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Session d'analyse"
        verbose_name_plural = "Sessions d'analyse"
        indexes = [
            models.Index(fields=["-created_at", "mode"]),
            models.Index(fields=["status", "-created_at"]),
        ]
    
    def __str__(self):
        return f"{self.get_mode_display()} - {self.room_id[:8]} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"
    
    @property
    def is_completed(self):
        """Retourne True si l'analyse est terminée."""
        return self.status == "completed"
    
    @property
    def is_failed(self):
        """Retourne True si l'analyse a échoué."""
        return self.status == "failed"
    
    def get_agents_summary(self):
        """
        Retourne un résumé des agents ayant participé.
        Utile pour l'affichage dans l'admin Django.
        """
        if not self.result_json or "agents" not in self.result_json:
            return "Aucun agent"
        
        agents = self.result_json.get("agents", [])
        return f"{len(agents)} agents: " + ", ".join(a.get("name", "?") for a in agents[:3])
    
    get_agents_summary.short_description = "Agents"

# Made with Bob
