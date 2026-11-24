"""
Policy Loader for PMBOK Audit System.

Loads and merges audit policies from YAML configuration files with support
for policy hierarchy (user > department > company > built-in PMBOK).
"""

import json
from pathlib import Path
from typing import Dict, Optional

import yaml

from .audit_policy import AuditCheck, AuditCriterion, PolicyExtensibility, PolicySet


class PolicyLoader:
    """Loads and manages audit policies."""

    # Built-in PMBOK policies directory
    DEFAULT_POLICIES_DIR = Path(__file__).parent.parent / "config" / "policies"

    def __init__(self, policies_dir: Optional[Path] = None):
        """
        Initialize the policy loader.

        Args:
            policies_dir: Directory containing policy YAML files.
                         Defaults to pmbok/config/policies/
        """
        self.policies_dir = policies_dir or self.DEFAULT_POLICIES_DIR
        self._cache: Dict[str, PolicySet] = {}

    def load_policy(self, policy_name: str, use_cache: bool = True) -> PolicySet:
        """
        Load a policy by name.

        Supports hierarchical loading:
        - user/{policy_name}.yaml (highest priority)
        - departments/{dept_name}.yaml
        - {policy_name}.yaml (company/default level)
        - Built-in defaults

        Args:
            policy_name: Name of the policy to load (e.g., 'pmbok_standard', 'company_default')
            use_cache: Whether to use cached policies

        Returns:
            PolicySet object

        Raises:
            FileNotFoundError: If policy file not found
            yaml.YAMLError: If YAML is invalid
        """
        if use_cache and policy_name in self._cache:
            return self._cache[policy_name]

        # Try to load from hierarchy
        policy_paths = [
            self.policies_dir / "pmbok_standard.yaml",  # Always start with built-in
        ]

        # Add company-level policies
        if (self.policies_dir / f"{policy_name}.yaml").exists():
            policy_paths.append(self.policies_dir / f"{policy_name}.yaml")

        # Look for user-specific overrides
        user_override = self.policies_dir / "users" / f"{policy_name}.yaml"
        if user_override.exists():
            policy_paths.append(user_override)

        # Start with built-in, then merge overrides
        policy = None
        for path in policy_paths:
            if path.exists():
                loaded = self._load_yaml_policy(path)
                if policy is None:
                    policy = loaded
                else:
                    policy = self._merge_policies(policy, loaded)

        if policy is None:
            raise FileNotFoundError(
                f"Policy '{policy_name}' not found in {self.policies_dir}"
            )

        if use_cache:
            self._cache[policy_name] = policy

        return policy

    def load_policy_for_context(
        self,
        policy_name: str,
        department: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> PolicySet:
        """
        Load a policy with department and user overrides.

        Hierarchy: user > department > company > built-in

        Args:
            policy_name: Base policy name
            department: Department name for department-level overrides
            user_id: User ID for user-level overrides

        Returns:
            Merged PolicySet
        """
        # Start with base policy
        policy = self.load_policy(policy_name, use_cache=True)

        # Apply department overrides
        if department:
            dept_path = self.policies_dir / "departments" / f"{department}.yaml"
            if dept_path.exists():
                dept_policy = self._load_yaml_policy(dept_path)
                policy = self._merge_policies(policy, dept_policy)

        # Apply user overrides
        if user_id:
            user_path = self.policies_dir / "users" / f"{user_id}.yaml"
            if user_path.exists():
                user_policy = self._load_yaml_policy(user_path)
                policy = self._merge_policies(policy, user_policy)

        return policy

    def list_available_policies(self) -> list[str]:
        """
        List all available policy names.

        Returns:
            List of policy names (without .yaml extension)
        """
        if not self.policies_dir.exists():
            return []

        policies = []
        for path in self.policies_dir.glob("*.yaml"):
            policies.append(path.stem)

        return sorted(policies)

    def _load_yaml_policy(self, path: Path) -> PolicySet:
        """
        Load and parse a YAML policy file.

        Args:
            path: Path to YAML file

        Returns:
            PolicySet object

        Raises:
            yaml.YAMLError: If YAML is invalid
        """
        with open(path, "r") as f:
            data = yaml.safe_load(f)

        return self._parse_policy_dict(data)

    def _parse_policy_dict(self, data: dict) -> PolicySet:
        """
        Parse a policy dictionary into PolicySet.

        Args:
            data: Dictionary loaded from YAML

        Returns:
            PolicySet object
        """
        criteria = []
        for criterion_data in data.get("criteria", []):
            checks = []
            for check_data in criterion_data.get("checks", []):
                check = AuditCheck(
                    code=check_data.get("code", ""),
                    description=check_data.get("description", ""),
                    check_type=check_data.get("type", "content"),
                    parameters=check_data.get("parameters", {}),
                    severity_if_failed=check_data.get("severity", "WARNING"),
                )
                checks.append(check)

            criterion = AuditCriterion(
                code=criterion_data.get("code", ""),
                name=criterion_data.get("name", ""),
                description=criterion_data.get("description", ""),
                weight=float(criterion_data.get("weight", 0.0)),
                checks=checks,
                knowledge_areas=criterion_data.get("knowledge_areas", []),
                process_groups=criterion_data.get("process_groups", []),
            )
            criteria.append(criterion)

        extensibility_data = data.get("extensibility", {})
        extensibility = PolicyExtensibility(
            allow_custom_checks=extensibility_data.get("allow_custom_checks", True),
            allow_custom_criteria=extensibility_data.get("allow_custom_criteria", True),
            allow_override_weights=extensibility_data.get("allow_override_weights", True),
        )

        policy = PolicySet(
            name=data.get("name", ""),
            description=data.get("description", ""),
            version=data.get("version", "1.0.0"),
            criteria=criteria,
            scoring_method=data.get("scoring_method", "weighted_average"),
            confidence_method=data.get("confidence_method", "combined"),
            iso_standards=data.get("iso_standards", []),
            extensibility=extensibility,
            parent_policy=data.get("parent_policy", None),
        )

        return policy

    def _merge_policies(self, base: PolicySet, override: PolicySet) -> PolicySet:
        """
        Merge two policies with override taking precedence.

        Args:
            base: Base policy
            override: Override policy

        Returns:
            Merged PolicySet
        """
        # Create merged policy starting from base
        merged = PolicySet(
            name=override.name or base.name,
            description=override.description or base.description,
            version=override.version or base.version,
            criteria=base.criteria.copy(),
            scoring_method=override.scoring_method or base.scoring_method,
            confidence_method=override.confidence_method or base.confidence_method,
            iso_standards=base.iso_standards + override.iso_standards,
            extensibility=override.extensibility or base.extensibility,
            parent_policy=base.name,
        )

        # Override or add criteria from override policy
        for override_criterion in override.criteria:
            # Find matching criterion in base
            existing = merged.get_criterion(override_criterion.code)
            if existing:
                # Update existing criterion
                existing.name = override_criterion.name or existing.name
                existing.description = override_criterion.description or existing.description
                if override_criterion.weight > 0:
                    existing.weight = override_criterion.weight
                if override_criterion.checks:
                    existing.checks = override_criterion.checks
            else:
                # Add new criterion
                merged.criteria.append(override_criterion)

        return merged
