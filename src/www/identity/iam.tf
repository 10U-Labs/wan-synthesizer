locals {
  product      = "wan-synthesizer"
  account      = module.common.aws_account_id
  region       = module.common.aws_region
  state_bucket = "arn:aws:s3:::${module.common.state_bucket}"
  site_bucket  = "arn:aws:s3:::www-10ulabs-com"
  distribution = "arn:aws:cloudfront::${local.account}:distribution/E2QC507LFNT58H"
  self         = "arn:aws:iam::${local.account}:role/${local.role_name}"
  api_key      = "arn:aws:ssm:${local.region}:${local.account}:parameter/api.10ulabs.com/api-key"
}

data "aws_iam_policy_document" "state" {
  statement {
    sid       = "ListTheStateBucket"
    actions   = ["s3:ListBucket"]
    resources = [local.state_bucket]
  }

  statement {
    sid       = "ReadWriteAndLockThisRepositoryState"
    actions   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"]
    resources = ["${local.state_bucket}/${local.product}/*"]
  }
}

data "aws_iam_policy_document" "site" {
  statement {
    sid       = "ListTheSiteUnderTheProductPrefix"
    actions   = ["s3:ListBucket"]
    resources = [local.site_bucket]

    condition {
      test     = "StringLike"
      variable = "s3:prefix"
      values   = ["${local.product}/*"]
    }
  }

  statement {
    sid       = "SyncTheSpaUnderTheProductPrefix"
    actions   = ["s3:PutObject", "s3:DeleteObject"]
    resources = ["${local.site_bucket}/${local.product}/*"]
  }

  statement {
    sid       = "FindTheSiteDistribution"
    actions   = ["cloudfront:ListDistributions"]
    resources = ["*"]
  }

  statement {
    sid = "InvalidateTheSiteDistribution"
    actions = [
      "cloudfront:GetDistribution",
      "cloudfront:CreateInvalidation",
      "cloudfront:GetInvalidation",
    ]
    resources = [local.distribution]
  }
}

data "aws_iam_policy_document" "self" {
  statement {
    sid = "ReconcileThisRole"
    actions = [
      "iam:GetRole",
      "iam:UpdateRole",
      "iam:UpdateRoleDescription",
      "iam:UpdateAssumeRolePolicy",
      "iam:ListRolePolicies",
      "iam:GetRolePolicy",
      "iam:PutRolePolicy",
      "iam:DeleteRolePolicy",
      "iam:ListAttachedRolePolicies",
      "iam:DetachRolePolicy",
      "iam:ListInstanceProfilesForRole",
      "iam:TagRole",
      "iam:UntagRole",
    ]
    resources = [local.self]
  }

  statement {
    sid       = "ReadTheGitHubProvider"
    actions   = ["iam:GetOpenIDConnectProvider"]
    resources = [data.aws_iam_openid_connect_provider.github.arn]
  }
}

data "aws_iam_policy_document" "api" {
  statement {
    sid       = "ReadTheApiKey"
    actions   = ["ssm:GetParameter"]
    resources = [local.api_key]
  }
}

resource "aws_iam_role_policy" "state" {
  name   = "State"
  role   = aws_iam_role.deploy.id
  policy = data.aws_iam_policy_document.state.json
}

resource "aws_iam_role_policy" "site" {
  name   = "Site"
  role   = aws_iam_role.deploy.id
  policy = data.aws_iam_policy_document.site.json
}

resource "aws_iam_role_policy" "self" {
  name   = "Self"
  role   = aws_iam_role.deploy.id
  policy = data.aws_iam_policy_document.self.json
}

resource "aws_iam_role_policy" "api" {
  name   = "Api"
  role   = aws_iam_role.deploy.id
  policy = data.aws_iam_policy_document.api.json
}
