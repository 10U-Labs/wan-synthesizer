locals {
  product      = "wan-synthesizer"
  account      = module.common.aws_account_id
  region       = module.common.aws_region
  state_bucket = "arn:aws:s3:::${module.common.state_bucket}"
  store_bucket = "arn:aws:s3:::${local.product}-store-${local.region}"
  site_bucket  = "arn:aws:s3:::www-10ulabs-com"
  distribution = "arn:aws:cloudfront::${local.account}:distribution/E2QC507LFNT58H"
  functions    = "arn:aws:lambda:${local.region}:${local.account}:function:${local.product}-*"
  layers       = "arn:aws:lambda:${local.region}:${local.account}:layer:${local.product}-*"
  log_groups   = "arn:aws:logs:${local.region}:${local.account}:log-group:/aws/lambda/${local.product}-*"
  log_listing  = "arn:aws:logs:${local.region}:${local.account}:log-group::log-stream:"
  lambda_roles = "arn:aws:iam::${local.account}:role/${local.product}-*"
  gateway_role = "arn:aws:iam::${local.account}:role/aws-service-role/ops.apigateway.amazonaws.com/AWSServiceRoleForAPIGateway"
  rest_apis    = "arn:aws:apigateway:${local.region}::/restapis"
  parameters   = "arn:aws:ssm:${local.region}:${local.account}:parameter/${local.product}/*"
  api_key      = "arn:aws:ssm:${local.region}:${local.account}:parameter/${local.product}/api-key"
  self         = "arn:aws:iam::${local.account}:role/${local.role_name}"
  seed_role    = "arn:aws:iam::${local.account}:role/${local.seed_role_name}"
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

data "aws_iam_policy_document" "store" {
  statement {
    sid = "DeclareTheStore"
    actions = [
      "s3:CreateBucket",
      "s3:ListBucket",
      "s3:ListBucketVersions",
      "s3:GetAccelerateConfiguration",
      "s3:GetBucketAcl",
      "s3:GetBucketCORS",
      "s3:GetBucketLogging",
      "s3:GetBucketObjectLockConfiguration",
      "s3:GetBucketPolicy",
      "s3:GetBucketPublicAccessBlock",
      "s3:PutBucketPublicAccessBlock",
      "s3:GetBucketRequestPayment",
      "s3:GetBucketTagging",
      "s3:PutBucketTagging",
      "s3:GetBucketVersioning",
      "s3:PutBucketVersioning",
      "s3:GetBucketWebsite",
      "s3:GetEncryptionConfiguration",
      "s3:GetLifecycleConfiguration",
      "s3:PutLifecycleConfiguration",
      "s3:GetReplicationConfiguration",
    ]
    resources = [local.store_bucket]
  }
}

data "aws_iam_policy_document" "functions" {
  statement {
    sid = "DeclareTheHandlers"
    actions = [
      "lambda:CreateFunction",
      "lambda:DeleteFunction",
      "lambda:GetFunction",
      "lambda:GetFunctionCodeSigningConfig",
      "lambda:ListVersionsByFunction",
      "lambda:UpdateFunctionCode",
      "lambda:UpdateFunctionConfiguration",
      "lambda:GetPolicy",
      "lambda:AddPermission",
      "lambda:RemovePermission",
      "lambda:GetFunctionEventInvokeConfig",
      "lambda:PutFunctionEventInvokeConfig",
      "lambda:UpdateFunctionEventInvokeConfig",
      "lambda:DeleteFunctionEventInvokeConfig",
      "lambda:ListTags",
      "lambda:TagResource",
      "lambda:UntagResource",
    ]
    resources = [local.functions]
  }

  statement {
    sid = "PublishTheSolverLayer"
    actions = [
      "lambda:PublishLayerVersion",
      "lambda:GetLayerVersion",
      "lambda:DeleteLayerVersion",
    ]
    resources = [local.layers, "${local.layers}:*"]
  }

  statement {
    sid       = "ListEveryFunctionToFindALeftover"
    actions   = ["lambda:ListFunctions"]
    resources = ["*"]
  }

  statement {
    sid       = "DescribeLogGroupsOnTheArnIamEvaluatesItAgainst"
    actions   = ["logs:DescribeLogGroups"]
    resources = [local.log_listing]
  }

  statement {
    sid = "KeepTheHandlersLogGroups"
    actions = [
      "logs:CreateLogGroup",
      "logs:DeleteLogGroup",
      "logs:PutRetentionPolicy",
      "logs:ListTagsForResource",
      "logs:TagResource",
      "logs:UntagResource",
    ]
    resources = [local.log_groups]
  }
}

data "aws_iam_policy_document" "roles" {
  statement {
    sid = "DeclareTheHandlersRoles"
    actions = [
      "iam:CreateRole",
      "iam:DeleteRole",
      "iam:GetRole",
      "iam:UpdateAssumeRolePolicy",
      "iam:ListRolePolicies",
      "iam:GetRolePolicy",
      "iam:PutRolePolicy",
      "iam:DeleteRolePolicy",
      "iam:ListAttachedRolePolicies",
      "iam:AttachRolePolicy",
      "iam:DetachRolePolicy",
      "iam:ListInstanceProfilesForRole",
      "iam:TagRole",
      "iam:UntagRole",
    ]
    resources = [local.lambda_roles]
  }

  statement {
    sid = "DeclareTheSeedRole"
    actions = [
      "iam:CreateRole",
      "iam:DeleteRole",
      "iam:GetRole",
      "iam:UpdateRole",
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
    resources = [local.seed_role]
  }

  statement {
    sid       = "HandTheHandlersRolesToLambdaAlone"
    actions   = ["iam:PassRole"]
    resources = [local.lambda_roles]

    condition {
      test     = "StringEquals"
      variable = "iam:PassedToService"
      values   = ["lambda.amazonaws.com"]
    }
  }

  statement {
    sid       = "LetApiGatewayAskForItsServiceRole"
    actions   = ["iam:CreateServiceLinkedRole"]
    resources = [local.gateway_role]

    condition {
      test     = "StringEquals"
      variable = "iam:AWSServiceName"
      values   = ["ops.apigateway.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "routing" {
  statement {
    sid = "DeclareTheApi"
    actions = [
      "apigateway:GET",
      "apigateway:POST",
      "apigateway:PUT",
      "apigateway:PATCH",
      "apigateway:DELETE",
    ]
    resources = [
      local.rest_apis,
      "${local.rest_apis}/*",
      "arn:aws:apigateway:${local.region}::/tags/*",
    ]
  }

  statement {
    sid = "KeepTheProductsParameters"
    actions = [
      "ssm:PutParameter",
      "ssm:GetParameter",
      "ssm:DeleteParameter",
      "ssm:ListTagsForResource",
      "ssm:AddTagsToResource",
      "ssm:RemoveTagsFromResource",
    ]
    resources = [local.parameters]
  }

  statement {
    sid       = "DescribeParametersToReadATier"
    actions   = ["ssm:DescribeParameters"]
    resources = ["*"]
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
    sid       = "InvalidateTheSiteDistribution"
    actions   = ["cloudfront:GetDistribution", "cloudfront:CreateInvalidation"]
    resources = [local.distribution]
  }
}

data "aws_iam_policy_document" "self" {
  statement {
    sid = "ReconcileThisRole"
    actions = [
      "iam:GetRole",
      "iam:UpdateRole",
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

data "aws_iam_policy_document" "seed_key" {
  statement {
    sid       = "ReadTheApiKeyAlone"
    actions   = ["ssm:GetParameter"]
    resources = [local.api_key]
  }
}

resource "aws_iam_role_policy" "state" {
  name   = "State"
  role   = aws_iam_role.deploy.id
  policy = data.aws_iam_policy_document.state.json
}

resource "aws_iam_role_policy" "store" {
  name   = "Store"
  role   = aws_iam_role.deploy.id
  policy = data.aws_iam_policy_document.store.json
}

resource "aws_iam_role_policy" "functions" {
  name   = "Functions"
  role   = aws_iam_role.deploy.id
  policy = data.aws_iam_policy_document.functions.json
}

resource "aws_iam_role_policy" "roles" {
  name   = "Roles"
  role   = aws_iam_role.deploy.id
  policy = data.aws_iam_policy_document.roles.json
}

resource "aws_iam_role_policy" "routing" {
  name   = "Routing"
  role   = aws_iam_role.deploy.id
  policy = data.aws_iam_policy_document.routing.json
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

resource "aws_iam_role_policy" "seed_key" {
  name   = "SeedKey"
  role   = aws_iam_role.seed.id
  policy = data.aws_iam_policy_document.seed_key.json
}
